(() => {
  const chips = document.querySelectorAll('[data-grade]');
  const items = document.querySelectorAll('[data-grades]');
  const cards = document.querySelectorAll('.author-card[data-grades]');
  const summary = document.querySelector('[data-map-summary]');
  const emptyNote = document.querySelector('[data-grade-empty]');
  const resetButton = document.querySelector('[data-grade-reset]');
  const map = document.getElementById('map');

  if (!chips.length || !summary) {
    return;
  }

  const defaultSummary = summary.textContent;

  const plural = (count, one, few, many) => {
    const mod10 = count % 10;
    const mod100 = count % 100;
    if (mod10 === 1 && mod100 !== 11) return one;
    if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
    return many;
  };

  const matches = (element, grade) => !grade || element.dataset.grades.split(' ').includes(grade);

  const apply = (grade) => {
    chips.forEach((chip) => {
      const active = chip.dataset.grade === grade;
      chip.classList.toggle('is-active', active);
      chip.setAttribute('aria-pressed', String(active));
    });

    items.forEach((item) => {
      item.hidden = !matches(item, grade);
    });

    const count = [...cards].filter((card) => matches(card, grade)).length;

    if (!grade) {
      summary.textContent = defaultSummary;
    } else if (count) {
      summary.textContent = `${grade} класс: ${count} ${plural(count, 'автор', 'автора', 'авторов')}`;
    } else {
      summary.textContent = `Для ${grade} класса авторы пока не отмечены`;
    }

    emptyNote.hidden = !grade || count > 0;
    emptyNote.textContent = grade ? `Для ${grade} класса авторы пока не отмечены.` : '';
    resetButton.hidden = !grade;
  };

  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      const grade = chip.classList.contains('is-active') ? '' : chip.dataset.grade;
      apply(grade);
      if (grade) {
        map.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  resetButton.addEventListener('click', () => apply(''));
})();
