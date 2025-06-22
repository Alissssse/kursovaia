document.addEventListener('DOMContentLoaded', function() {
    // Находим поле цены
    const priceField = document.querySelector('#id_price');
    
    if (priceField) {
        // Добавляем обработчик события при изменении значения
        priceField.addEventListener('change', function() {
            const price = parseFloat(this.value);
            
            // Проверяем, что цена положительная
            if (price < 0) {
                alert('Цена не может быть отрицательной!');
                this.value = 0;
            }
            
            // Проверяем, что цена не слишком высокая
            if (price > 100000) {
                alert('Цена кажется слишком высокой. Пожалуйста, проверьте значение.');
            }
        });
        
        // Добавляем подсказку при наведении
        priceField.title = 'Введите положительное число. Рекомендуемый диапазон: 0-100000';
    }
}); 