// Функция для получения CSRF токена
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
    // Добавление рыбы
    const fishForm = document.getElementById('fish-form');
    if (fishForm) {
        fishForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch('', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const newRow = `
                        <tr data-fish-id="${data.fish.id}">
                            <td>${data.fish.species}</td>
                            <td>${data.fish.length1}</td>
                            <td>${data.fish.length2}</td>
                            <td>${data.fish.length3}</td>
                            <td>${data.fish.height}</td>
                            <td>${data.fish.width}</td>
                            <td class="predicted-weight">-</td>
                            <td>
                                <button class="btn btn-danger btn-sm delete-btn" data-fish-id="${data.fish.id}">
                                    <i class="fas fa-trash-alt"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                    document.querySelector('#fish-table tbody').insertAdjacentHTML('beforeend', newRow);
                    this.reset();
                } else {
                    alert('Ошибка: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Произошла ошибка при добавлении рыбы');
            });
        });
    }

    // Удаление рыбы
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-btn')) {
            const button = e.target.closest('.delete-btn');
            const fishId = button.dataset.fishId;
            const row = button.closest('tr');
            
            if (confirm('Вы уверены, что хотите удалить эту рыбу?')) {
                fetch(`/delete/${fishId}/`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        row.remove();
                    } else {
                        alert('Ошибка при удалении');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Произошла ошибка при удалении');
                });
            }
        }
    });

    // Прогнозирование веса
    document.getElementById('predict-btn').addEventListener('click', function() {
        const fishRows = document.querySelectorAll('#fish-table tbody tr');
        if (fishRows.length === 0) {
            alert('Нет данных для прогнозирования');
            return;
        }
        
        const fishData = Array.from(fishRows).map(row => {
            // Важно: названия ключей должны точно соответствовать ожидаемым в views.py
            return {
                Species: row.cells[0].textContent,
                Length1: row.cells[1].textContent,
                Length2: row.cells[2].textContent,
                Length3: row.cells[3].textContent,
                Height: row.cells[4].textContent,
                Width: row.cells[5].textContent
            };
        });
        
        fetch('/predict/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({fish_data: fishData})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                data.predictions.forEach((pred, index) => {
                    const weightCell = fishRows[index].querySelector('.predicted-weight');
                    weightCell.textContent = pred.toFixed(2) + ' г';
                    weightCell.style.color = '#28a745';
                    weightCell.style.fontWeight = 'bold';
                });
            } else {
                alert('Ошибка: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Произошла ошибка при прогнозировании');
        });
    });
});