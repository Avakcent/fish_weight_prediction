from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse
from io import BytesIO
import os
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
import joblib
from .forms import FishDataForm, UploadFileForm
from .models import FishData
import pandas as pd
import numpy as np
import json
from sklearn.linear_model import LinearRegression
from django.views.decorators.csrf import csrf_exempt

# Константы
VALID_SPECIES = ['Bream', 'Parkki', 'Perch', 'Pike', 'Roach', 'Smelt', 'Whitefish']
MODEL_PATH = 'fish_model.pkl'

# Загрузка/обучение модели
def load_or_train_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    
    train_df = pd.read_csv('Fish.csv')
    train_df = train_df[train_df['Species'].isin(VALID_SPECIES)]
    
    # Явно указываем нужные столбцы с правильными названиями
    X = train_df[['Species', 'Length1', 'Length2', 'Length3', 'Height', 'Width']]
    y = train_df['Weight']
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('species', OneHotEncoder(categories=[VALID_SPECIES]), ['Species'])
        ],
        remainder='passthrough'
    )
    
    model = Pipeline([
        ('preprocessor', preprocessor),
        ('model', LinearRegression())
    ])
    
    model.fit(X, y)
    joblib.dump(model, MODEL_PATH)
    return model

# Загружаем модель при старте
model_pipeline = load_or_train_model()

# Параметры модели
MODEL_PARAMS = {
    'name': 'Линейная регрессия',
    'rmse': 68.76,
    'mae': 54.51,
    'r2': 0.9668,
    'valid_species': VALID_SPECIES
}

def predict_weight(data):
    df = pd.DataFrame(data)
    df = df[df['Species'].isin(VALID_SPECIES)]
    if df.empty:
        return np.array([])
    return model_pipeline.predict(df)

def predict_weight_ajax(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            fish_data = data.get('fish_data', [])
            
            if not fish_data:
                return JsonResponse({'success': False, 'error': 'Нет данных для прогноза'})
            
            # Создаем DataFrame с ТОЧНО ТАКИМИ ЖЕ названиями столбцов, как при обучении
            df = pd.DataFrame([{
                'Species': item['Species'],
                'Length1': float(item['Length1']),
                'Length2': float(item['Length2']),
                'Length3': float(item['Length3']),
                'Height': float(item['Height']),
                'Width': float(item['Width'])
            } for item in fish_data])
            
            # Прогнозирование
            predictions = model_pipeline.predict(df)
            
            return JsonResponse({
                'success': True,
                'predictions': [max(0, float(p)) for p in predictions]  # Не допускаем отрицательный вес
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Ошибка прогнозирования: {str(e)}'
            })
    return JsonResponse({'success': False, 'error': 'Неверный запрос'})

def update_weight(request, fish_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            fish = FishData.objects.get(id=fish_id)
            fish.predicted_weight = float(data['weight'])
            fish.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Неверный запрос'})

def home(request):
    if request.method == 'POST':
        form = FishDataForm(request.POST)
        if form.is_valid():
            fish = form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'fish': {
                        'id': fish.id,
                        'species': fish.species,
                        'length1': fish.length1,
                        'length2': fish.length2,
                        'length3': fish.length3,
                        'height': fish.height,
                        'width': fish.width
                    }
                })
            return redirect('home')
    
    form = FishDataForm()
    fish_data = FishData.objects.all()
    return render(request, 'prediction/home.html', {
        'form': form,
        'fish_data': fish_data,
        'model_params': MODEL_PARAMS
    })

def delete_fish(request, fish_id):
    if request.method == 'POST':
        fish = get_object_or_404(FishData, id=fish_id)
        fish.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('home')
    return JsonResponse({'success': False})


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES['file']
                df = pd.read_excel(file, engine='openpyxl')
                
                required_columns = ['Species', 'Length1', 'Length2', 'Length3', 'Height', 'Width']
                if not all(col in df.columns for col in required_columns):
                    return render(request, 'prediction/upload.html', {
                        'form': form,
                        'error': 'Файл должен содержать все требуемые колонки'
                    })
                
                for col in ['Length1', 'Length2', 'Length3', 'Height', 'Width']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    if df[col].isnull().any() or (df[col] <= 0).any():
                        return render(request, 'prediction/upload.html', {
                            'form': form,
                            'error': f'Некорректные значения в колонке {col}'
                        })
                
                request.session['uploaded_data'] = df.to_dict('records')
                return redirect('predict_from_upload')
                
            except Exception as e:
                return render(request, 'prediction/upload.html', {
                    'form': form,
                    'error': f'Ошибка обработки файла: {str(e)}'
                })
    else:
        form = UploadFileForm()
    
    return render(request, 'prediction/upload.html', {'form': form})

def predict_from_upload(request):
    if 'uploaded_data' not in request.session:
        return redirect('upload')
    
    data = request.session['uploaded_data']
    df = pd.DataFrame(data)
    
    # Проверяем и переименовываем столбцы
    column_mapping = {
        'length1': 'Length1',
        'length2': 'Length2',
        'length3': 'Length3',
        'height': 'Height',
        'width': 'Width'
    }
    df = df.rename(columns=column_mapping)
    
    # Проверяем наличие всех столбцов
    required_columns = ['Species', 'Length1', 'Length2', 'Length3', 'Height', 'Width']
    if not all(col in df.columns for col in required_columns):
        return render(request, 'prediction/upload.html', {
            'error': 'Файл должен содержать все необходимые столбцы'
        })
    
    # Прогнозирование
    try:
        predictions = model_pipeline.predict(df[required_columns])
        df['PredictedWeight'] = [max(0, p) for p in predictions]  # Не допускаем отрицательный вес
    except Exception as e:
        return render(request, 'prediction/upload.html', {
            'error': f'Ошибка прогнозирования: {str(e)}'
        })
    
    # Сохраняем результаты
    results = []
    for i, row in enumerate(data):
        result = row.copy()
        result['PredictedWeight'] = round(float(predictions[i]), 2)
        results.append(result)
    
    # Обработка скачивания
    if request.method == 'POST' and 'download' in request.POST:
        output_df = pd.DataFrame(results)
        output = BytesIO()
        output_df.to_excel(output, index=False)
        output.seek(0)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="fish_predictions.xlsx"'
        return response
    
    return render(request, 'prediction/predict_results.html', {'results': results})