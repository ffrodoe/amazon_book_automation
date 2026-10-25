document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const inputFolder = document.getElementById('inputFolder');
  const btnScan = document.getElementById('btnScan');
  const formatCards = document.querySelectorAll('.format-card');
  const introSlider = document.getElementById('introCount');
  const introVal = document.getElementById('introCountVal');
  const btnBuild = document.getElementById('btnBuild');
  const btnBuildText = document.getElementById('btnBuildText');

  const statImagesCount = document.getElementById('statImagesCount');
  const statPagesCount = document.getElementById('statPagesCount');
  const statRightSideCount = document.getElementById('statRightSideCount');
  const statBlankCount = document.getElementById('statBlankCount');
  const pagesGrid = document.getElementById('pagesGrid');

  const resultBox = document.getElementById('resultBox');
  const resultFileName = document.getElementById('resultFileName');
  const resultPages = document.getElementById('resultPages');
  const resultSize = document.getElementById('resultSize');
  const btnOpenFolder = document.getElementById('btnOpenFolder');
  const btnDownload = document.getElementById('btnDownload');

  let currentPlan = null;
  let lastGeneratedPdfPath = null;

  // Selected format
  function getSelectedFormat() {
    const checked = document.querySelector('input[name="bookFormat"]:checked');
    return checked ? checked.value : 'a4';
  }

  // Format cards toggle
  formatCards.forEach(card => {
    card.addEventListener('click', () => {
      formatCards.forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      const radio = card.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
      scanFolder();
    });
  });

  // Slider change
  introSlider.addEventListener('input', (e) => {
    const val = e.target.value;
    introVal.textContent = `${val} ${val == 1 ? 'страница' : val < 5 ? 'страницы' : 'страниц'}`;
  });

  introSlider.addEventListener('change', () => {
    scanFolder();
  });

  // Scan folder
  async function scanFolder() {
    const folderPath = inputFolder.value.trim();
    if (!folderPath) return;

    const format = getSelectedFormat();
    const introCount = parseInt(introSlider.value, 10);

    btnScan.disabled = true;
    btnScan.querySelector('span').textContent = 'Поиск...';

    try {
      const response = await fetch(`/api/scan?path=${encodeURIComponent(folderPath)}&format=${format}&intro_count=${introCount}`);
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Не удалось просканировать папку');
      }

      const data = await response.json();
      currentPlan = data;
      renderPlan(data);
    } catch (err) {
      alert(`Ошибка при анализе папки: ${err.message}`);
    } finally {
      btnScan.disabled = false;
      btnScan.querySelector('span').textContent = 'Анализ';
    }
  }

  // Render plan in UI
  function renderPlan(data) {
    // Stats
    statImagesCount.textContent = data.total_images;
    statPagesCount.textContent = `${data.total_pages} стр.`;

    const blankCount = data.pages.filter(p => p.is_blank).length;
    const rightSideCount = data.pages.filter(p => p.is_recto && !p.is_blank).length;

    statBlankCount.textContent = blankCount;
    statRightSideCount.textContent = rightSideCount;

    // Render Grid
    pagesGrid.innerHTML = '';
    const isSquare = data.format === '8.5x8.5';

    data.pages.forEach(p => {
      const card = document.createElement('div');
      card.className = `page-card ${isSquare ? 'square-ratio' : ''}`;

      const sideLabel = p.is_recto ? 'Справа (Recto)' : 'Слева (Verso)';
      const sideTagClass = p.is_recto ? 'tag-recto' : 'tag-verso';

      let contentHtml = '';
      if (p.is_blank) {
        contentHtml = `
          <div class="blank-placeholder">
            <span>🛡️</span>
            <span>Чистый лист</span>
            <span style="opacity: 0.6">Защита от маркера</span>
          </div>
        `;
      } else {
        const imgUrl = `/api/image?path=${encodeURIComponent(p.image_path)}`;
        contentHtml = `<img src="${imgUrl}" alt="${p.image_name}" loading="lazy" />`;
      }

      card.innerHTML = `
        <div class="page-thumb-wrapper">
          ${contentHtml}
        </div>
        <div class="page-meta">
          <span class="page-num">Стр. ${p.page_number}</span>
          <span class="page-side-tag ${sideTagClass}">${p.is_recto ? 'Правая' : 'Левая'}</span>
        </div>
        <div class="page-title-label" title="${p.label}">
          ${p.is_blank ? 'Пустая страница' : (p.image_name || p.label)}
        </div>
      `;

      pagesGrid.appendChild(card);
    });
  }

  // Build PDF
  btnBuild.addEventListener('click', async () => {
    const folderPath = inputFolder.value.trim();
    if (!folderPath) {
      alert('Укажите папку с картинками!');
      return;
    }

    const format = getSelectedFormat();
    const introCount = parseInt(introSlider.value, 10);

    btnBuild.disabled = true;
    btnBuildText.textContent = 'Сборка PDF (высокое качество 300 DPI)...';

    try {
      const response = await fetch('/api/build', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder_path: folderPath,
          format: format,
          intro_count: introCount
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Ошибка при генерации PDF');
      }

      const res = await response.json();
      lastGeneratedPdfPath = res.output_path;

      // Show Result
      resultBox.classList.remove('hidden');
      resultFileName.textContent = res.file_name;
      resultPages.textContent = `${res.total_pages} страниц (чётное число для KDP)`;
      resultSize.textContent = `${res.size_mb} MB`;

      btnDownload.href = `/api/download?path=${encodeURIComponent(res.output_path)}`;

      // Scroll result into view
      resultBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (err) {
      alert(`Ошибка генерации: ${err.message}`);
    } finally {
      btnBuild.disabled = false;
      btnBuildText.textContent = 'Собрать PDF для Amazon KDP';
    }
  });

  // Open folder in Explorer
  btnOpenFolder.addEventListener('click', async () => {
    if (!lastGeneratedPdfPath) return;
    try {
      await fetch(`/api/open-folder?path=${encodeURIComponent(lastGeneratedPdfPath)}`);
    } catch (e) {
      console.error(e);
    }
  });

  // Background Cleaning Tool
  const brightnessSlider = document.getElementById('brightnessSlider');
  const brightnessVal = document.getElementById('brightnessVal');
  const btnCleanBackground = document.getElementById('btnCleanBackground');
  const btnCleanText = document.getElementById('btnCleanText');
  const cleanStatus = document.getElementById('cleanStatus');

  if (brightnessSlider && brightnessVal) {
    brightnessSlider.addEventListener('input', (e) => {
      brightnessVal.textContent = `+${e.target.value} ед.`;
    });
  }

  if (btnCleanBackground) {
    btnCleanBackground.addEventListener('click', async () => {
      const folderPath = inputFolder.value.trim();
      if (!folderPath) {
        alert('Укажите папку с картинками!');
        return;
      }

      const offset = parseInt(brightnessSlider.value, 10) || 40;

      btnCleanBackground.disabled = true;
      btnCleanText.textContent = 'Очистка фона...';
      cleanStatus.classList.add('hidden');

      try {
        const response = await fetch('/api/clean-background', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            folder_path: folderPath,
            brightness_offset: offset
          })
        });

        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || 'Ошибка при очистке картинок');
        }

        const res = await response.json();
        cleanStatus.classList.remove('hidden');
        cleanStatus.innerHTML = `✓ Очищено <strong>${res.total_cleaned}</strong> картинок (фон #FFFFFF). Папка переключена на <strong>${res.relative_output_dir}</strong>`;

        // Switch active folder to cleaned and rescan
        inputFolder.value = res.relative_output_dir;
        scanFolder();
      } catch (err) {
        alert(`Ошибка очистки фона: ${err.message}`);
      } finally {
        btnCleanBackground.disabled = false;
        btnCleanText.textContent = 'Очистить фон картинок';
      }
    });
  }

  // Scan button trigger
  btnScan.addEventListener('click', scanFolder);

  // Initial scan on launch
  scanFolder();
});

