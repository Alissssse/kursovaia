document.addEventListener('DOMContentLoaded', function() {
    // Находим поле длительности
    const durationField = document.querySelector('#id_duration');
    
    if (durationField) {
        // Создаем и добавляем подсказку
        const helpText = document.createElement('p');
        helpText.className = 'help';
        helpText.style.color = '#666';
        helpText.style.fontSize = '12px';
        helpText.style.marginTop = '5px';
        durationField.parentNode.appendChild(helpText);
        
        // Обновляем текст подсказки при изменении значения
        durationField.addEventListener('change', function() {
            const duration = parseInt(this.value);
            let recommendation = '';
            
            if (duration <= 2) {
                recommendation = 'Короткий тур - подходит для быстрого осмотра достопримечательностей';
            } else if (duration <= 4) {
                recommendation = 'Средний тур - оптимально для детального осмотра района';
            } else if (duration <= 8) {
                recommendation = 'Длинный тур - можно посетить несколько районов';
            } else {
                recommendation = 'Полный день - подходит для комплексного изучения города';
            }
            
            helpText.textContent = recommendation;
        });
        
        // Вызываем событие change для начальной установки подсказки
        durationField.dispatchEvent(new Event('change'));
    }
}); 