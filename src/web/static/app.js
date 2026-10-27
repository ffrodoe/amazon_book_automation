document.addEventListener('DOMContentLoaded', () => {
  // ==========================================
  // Global Elements & State
  // ==========================================
  const inputFolder = document.getElementById('inputFolder');
  const btnBrowse = document.getElementById('btnBrowse');
  const btnScan = document.getElementById('btnScan');
  const formatCards = document.querySelectorAll('.format-card');

  // Tabs
  const tabBtnInterior = document.getElementById('tabBtnInterior');
  const tabBtnCover = document.getElementById('tabBtnCover');
  const tabBtnAplus = document.getElementById('tabBtnAplus');
  const tabInterior = document.getElementById('tabInterior');
  const tabCover = document.getElementById('tabCover');
  const tabAplus = document.getElementById('tabAplus');

  // Interior Elements
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
  const resultFilePath = document.getElementById('resultFilePath');
  const resultPages = document.getElementById('resultPages');
  const resultSize = document.getElementById('resultSize');
  const btnOpenFolder = document.getElementById('btnOpenFolder');
  const btnDownload = document.getElementById('btnDownload');

  const btnCropBorders = document.getElementById('btnCropBorders');
  const btnCropText = document.getElementById('btnCropText');
  const cropStatus = document.getElementById('cropStatus');
  const chkCropSkipIntro = document.getElementById('chkCropSkipIntro');
  const cropSkipCount = document.getElementById('cropSkipCount');
  const chkCropOverwrite = document.getElementById('chkCropOverwrite');
  const chkCropDebug = document.getElementById('chkCropDebug');

  const brightnessSlider = document.getElementById('brightnessSlider');
  const brightnessVal = document.getElementById('brightnessVal');
  const chkCleanOverwrite = document.getElementById('chkCleanOverwrite');
  const btnCleanBackground = document.getElementById('btnCleanBackground');
  const btnCleanText = document.getElementById('btnCleanText');
  const cleanStatus = document.getElementById('cleanStatus');

  // Cover Elements
  const frontDot = document.getElementById('frontDot');
  const frontCoverFilename = document.getElementById('frontCoverFilename');
  const backDot = document.getElementById('backDot');
  const backCoverFilename = document.getElementById('backCoverFilename');
  const coverStatusTip = document.getElementById('coverStatusTip');

  const inputSpineWidth = document.getElementById('inputSpineWidth');
  const btnRecalcSpine = document.getElementById('btnRecalcSpine');
  const spinePagesNote = document.getElementById('spinePagesNote');
  const inputSpineColor = document.getElementById('inputSpineColor');
  const inputSpineColorHex = document.getElementById('inputSpineColorHex');
  const colorSwatches = document.querySelectorAll('.color-swatch');

  const chosenThumbsGrid = document.getElementById('chosenThumbsGrid');
  const thumbsCountBadge = document.getElementById('thumbsCountBadge');
  const btnToggleGallery = document.getElementById('btnToggleGallery');
  const interiorGalleryDrawer = document.getElementById('interiorGalleryDrawer');
  const interiorGalleryGrid = document.getElementById('interiorGalleryGrid');
  const activeSlotHint = document.getElementById('activeSlotHint');

  const btnPreviewCover = document.getElementById('btnPreviewCover');
  const btnBuildCover = document.getElementById('btnBuildCover');
  const btnBuildCoverText = document.getElementById('btnBuildCoverText');

  const coverResultBox = document.getElementById('coverResultBox');
  const coverResultFilePath = document.getElementById('coverResultFilePath');
  const coverResultSize = document.getElementById('coverResultSize');
  const coverResultFormat = document.getElementById('coverResultFormat');
  const btnCoverOpenFolder = document.getElementById('btnCoverOpenFolder');
  const btnCoverDownload = document.getElementById('btnCoverDownload');

  const coverCanvasContainer = document.getElementById('coverCanvasContainer');
  const coverEmptyState = document.getElementById('coverEmptyState');
  const coverStage = document.getElementById('coverStage');
  const coverBackPane = document.getElementById('coverBackPane');
  const coverSpinePane = document.getElementById('coverSpinePane');
  const coverFrontPane = document.getElementById('coverFrontPane');
  const spineLabel = document.getElementById('spineLabel');
  const coverDimsBadge = document.getElementById('coverDimsBadge');

  // A+ Content Elements
  const aplusTemplatesCount = document.getElementById('aplusTemplatesCount');
  const aplusTemplatesFolderHint = document.getElementById('aplusTemplatesFolderHint');
  const btnBrowseAplusFolder = document.getElementById('btnBrowseAplusFolder');
  const aplusFilterPills = document.getElementById('aplusFilterPills');
  const aplusTemplatesGrid = document.getElementById('aplusTemplatesGrid');

  const aplusSlotsBadge = document.getElementById('aplusSlotsBadge');
  const btnAplusAutoSelect = document.getElementById('btnAplusAutoSelect');
  const btnAplusRandomSelect = document.getElementById('btnAplusRandomSelect');
  const aplusSlotsGrid = document.getElementById('aplusSlotsGrid');
  const aplusDrawerTitle = document.getElementById('aplusDrawerTitle');
  const aplusGalleryGrid = document.getElementById('aplusGalleryGrid');

  const chkAplusExportAmazon = document.getElementById('chkAplusExportAmazon');
  const chipFitContain = document.getElementById('chipFitContain');
  const chipFitCover = document.getElementById('chipFitCover');
  const aplusCustomName = document.getElementById('aplusCustomName');

  const btnAplusPreview = document.getElementById('btnAplusPreview');
  const btnAplusBuild = document.getElementById('btnAplusBuild');
  const btnAplusBuildText = document.getElementById('btnAplusBuildText');

  const aplusResultBox = document.getElementById('aplusResultBox');
  const aplusResultFolder = document.getElementById('aplusResultFolder');
  const aplusFilesList = document.getElementById('aplusFilesList');
  const btnAplusOpenFolder = document.getElementById('btnAplusOpenFolder');

  const aplusDimsBadge = document.getElementById('aplusDimsBadge');
  const aplusCanvasContainer = document.getElementById('aplusCanvasContainer');
  const aplusEmptyState = document.getElementById('aplusEmptyState');
  const aplusPreviewStage = document.getElementById('aplusPreviewStage');
  const aplusPreviewImg = document.getElementById('aplusPreviewImg');

  // State
  let currentPlan = null;
  let currentCoverDetails = null;
  let selectedThumbnails = [null, null, null, null];
  let activeSlotIndex = 0;
  let lastGeneratedInteriorPdf = null;
  let lastGeneratedCoverPdf = null;

  // A+ State
  let aplusTemplates = [];
  let selectedAplusTemplate = null;
  let aplusSelectedImages = [null, null, null, null];
  let aplusActiveSlot = 0;
  let aplusCustomFolder = null;
  let aplusFilter = 'all';
  let lastGeneratedAplusFiles = [];

  // ==========================================
  // Helper Functions
  // ==========================================
  function getSelectedFormat() {
    const checked = document.querySelector('input[name="bookFormat"]:checked');
    return checked ? checked.value : 'a4';
  }

  // ==========================================
  // Tab Switching
  // ==========================================
  function switchTab(target) {
    // 1. Unconditionally switch active classes on all tab buttons and panes
    document.querySelectorAll('.tabs-nav .tab-btn').forEach(btn => {
      const isTarget = (btn.dataset.target === target) ||
                       (btn.id === 'tabBtnInterior' && target === 'tabInterior') ||
                       (btn.id === 'tabBtnCover' && target === 'tabCover') ||
                       (btn.id === 'tabBtnAplus' && target === 'tabAplus');
      btn.classList.toggle('active', isTarget);
    });

    document.querySelectorAll('.tab-pane').forEach(pane => {
      pane.classList.toggle('active', pane.id === target);
    });

    // 2. Perform tab-specific loading safely
    try {
      if (target === 'tabCover') {
        const folder = inputFolder.value.trim();
        if (folder && (!currentCoverDetails || currentCoverDetails.folder_path !== folder)) {
          loadCoverDetails();
        }
      } else if (target === 'tabAplus') {
        initAplusTab();
      }
    } catch (err) {
      console.error('[Tabs] Error switching to ' + target, err);
    }
  }

  // Expose globally so inline HTML onclick and other callers can reach it
  window.switchTabHandler = switchTab;
  window.switchTab = switchTab;

  tabBtnInterior.addEventListener('click', () => switchTab('tabInterior'));
  tabBtnCover.addEventListener('click', () => switchTab('tabCover'));
  tabBtnAplus.addEventListener('click', () => switchTab('tabAplus'));

  // ==========================================
  // Format Selection
  // ==========================================
  formatCards.forEach(card => {
    card.addEventListener('click', () => {
      formatCards.forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      const radio = card.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
      syncProject();
    });
  });

  // ==========================================
  // Native Folder Browser Dialog
  // ==========================================
  btnBrowse.addEventListener('click', async () => {
    btnBrowse.disabled = true;
    try {
      const cur = encodeURIComponent(inputFolder.value.trim());
      const res = await fetch(`/api/browse-folder?current=${cur}`);
      if (res.ok) {
        const data = await res.json();
        if (!data.cancelled && data.path) {
          inputFolder.value = data.path;
          syncProject();
        }
      }
    } catch (e) {
      console.error('Error opening folder dialog:', e);
    } finally {
      btnBrowse.disabled = false;
    }
  });

  btnScan.addEventListener('click', () => syncProject());
  inputFolder.addEventListener('change', () => syncProject());

  // Synchronize both interior and cover data
  async function syncProject() {
    const folder = inputFolder.value.trim();
    if (!folder) return;

    try {
      localStorage.setItem('kdp_last_folder', folder);
    } catch (e) {}

    btnScan.disabled = true;
    btnScan.classList.add('spinning');

    try {
      await Promise.all([
        scanInteriorFolder(),
        loadCoverDetails()
      ]);
      if (aplusInitialized) {
        syncAplusWithCurrentBook();
      }
    } finally {
      btnScan.disabled = false;
      btnScan.classList.remove('spinning');
    }
  }

  // ==========================================
  // Interior Logic
  // ==========================================
  introSlider.addEventListener('input', (e) => {
    const val = e.target.value;
    introVal.textContent = `${val} ${val == 1 ? 'страница' : val < 5 ? 'страницы' : 'страниц'}`;
  });

  introSlider.addEventListener('change', () => scanInteriorFolder());

  async function scanInteriorFolder() {
    const folderPath = inputFolder.value.trim();
    if (!folderPath) return;

    const format = getSelectedFormat();
    const introCount = parseInt(introSlider.value, 10);

    try {
      const response = await fetch(`/api/scan?path=${encodeURIComponent(folderPath)}&format=${format}&intro_count=${introCount}`);
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Не удалось просканировать папку');
      }

      const data = await response.json();
      currentPlan = data;
      renderInteriorPlan(data);
    } catch (err) {
      console.warn('Scan interior error:', err.message);
    }
  }

  function renderInteriorPlan(data) {
    statImagesCount.textContent = data.total_images;
    statPagesCount.textContent = `${data.total_pages} стр.`;

    const blankCount = data.pages.filter(p => p.is_blank).length;
    const rightSideCount = data.pages.filter(p => p.is_recto && !p.is_blank).length;

    statBlankCount.textContent = blankCount;
    statRightSideCount.textContent = rightSideCount;

    pagesGrid.innerHTML = '';
    if (data.pages.length === 0) {
      pagesGrid.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">📂</div>
          <div class="empty-text">В папке не найдены иллюстрации раскрасок</div>
        </div>`;
      return;
    }

    data.pages.forEach(page => {
      const card = document.createElement('div');
      card.className = `page-card ${page.is_blank ? 'page-blank' : ''} ${page.is_recto ? 'side-recto' : 'side-verso'}`;

      if (page.is_blank) {
        card.innerHTML = `
          <div class="page-aspect-box">
            <div class="blank-icon">⬜</div>
          </div>
          <div class="page-meta">
            <span class="page-num-badge">Стр. ${page.page_number}</span>
            <span class="page-side-tag tag-verso">Левая (Verso)</span>
          </div>
          <div class="page-title-label">${page.label}</div>
        `;
      } else {
        const cacheBust = page.modified_time ? `&t=${page.modified_time}` : '';
        const previewUrl = `/api/image?path=${encodeURIComponent(page.image_path)}${cacheBust}`;
        card.innerHTML = `
          <div class="page-aspect-box">
            <img src="${previewUrl}" alt="${page.image_name}" loading="lazy">
          </div>
          <div class="page-meta">
            <span class="page-num-badge">Стр. ${page.page_number}</span>
            <span class="page-side-tag ${page.is_recto ? 'tag-recto' : 'tag-verso'}">
              ${page.is_recto ? 'Правая (Recto)' : 'Левая (Verso)'}
            </span>
          </div>
          <div class="page-title-label" title="${page.image_name}">${page.image_name}</div>
        `;
      }
      pagesGrid.appendChild(card);
    });
  }

  // Crop borders
  btnCropBorders.addEventListener('click', async () => {
    const folder = inputFolder.value.trim();
    if (!folder) return alert('Сначала укажите папку книги');

    btnCropBorders.disabled = true;
    btnCropText.textContent = 'Обработка и обрезка рамок...';
    cropStatus.classList.add('hidden');

    try {
      const skipCount = chkCropSkipIntro.checked ? parseInt(cropSkipCount.value, 10) : 0;
      const res = await fetch('/api/crop-borders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder_path: folder,
          overwrite: chkCropOverwrite.checked,
          debug: chkCropDebug.checked,
          skip_count: skipCount
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Ошибка при обрезке рамок');

      cropStatus.textContent = `✓ Готово! Обработано файлов: ${data.total_files}, удалены рамки у: ${data.cropped_count}.`;
      cropStatus.classList.remove('hidden');
      await syncProject();
    } catch (err) {
      alert(`Ошибка: ${err.message}`);
    } finally {
      btnCropBorders.disabled = false;
      btnCropText.textContent = 'Удалить рамки с картинок';
    }
  });

  // Whitening
  brightnessSlider.addEventListener('input', (e) => {
    brightnessVal.textContent = `+${e.target.value} ед.`;
  });

  btnCleanBackground.addEventListener('click', async () => {
    const folder = inputFolder.value.trim();
    if (!folder) return alert('Сначала укажите папку книги');

    btnCleanBackground.disabled = true;
    btnCleanText.textContent = 'Отбеливание фона...';
    cleanStatus.classList.add('hidden');

    try {
      const res = await fetch('/api/clean-background', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder_path: folder,
          brightness_offset: parseInt(brightnessSlider.value, 10),
          overwrite: chkCleanOverwrite.checked
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Ошибка очистки фона');

      cleanStatus.textContent = `✓ Фон очищен у ${data.total_cleaned} изображений (сдвиг +${data.brightness_offset} ед.)`;
      cleanStatus.classList.remove('hidden');
      await syncProject();
    } catch (err) {
      alert(`Ошибка: ${err.message}`);
    } finally {
      btnCleanBackground.disabled = false;
      btnCleanText.textContent = 'Очистить фон картинок';
    }
  });

  // Build Interior PDF
  btnBuild.addEventListener('click', async () => {
    const folder = inputFolder.value.trim();
    if (!folder) return alert('Укажите папку книги');

    btnBuild.disabled = true;
    btnBuildText.textContent = 'Сборка Interior PDF...';

    try {
      const res = await fetch('/api/build', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder_path: folder,
          format: getSelectedFormat(),
          intro_count: parseInt(introSlider.value, 10)
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Ошибка сборки PDF');

      lastGeneratedInteriorPdf = data.output_path;
      resultFilePath.textContent = data.file_name;
      resultPages.textContent = `${data.total_pages} стр.`;
      resultSize.textContent = `${data.size_mb} MB`;
      btnDownload.href = `/api/download?path=${encodeURIComponent(data.output_path)}`;
      resultBox.classList.remove('hidden');
    } catch (err) {
      alert(`Ошибка: ${err.message}`);
    } finally {
      btnBuild.disabled = false;
      btnBuildText.textContent = 'Собрать Interior PDF для Amazon KDP';
    }
  });

  btnOpenFolder.addEventListener('click', async () => {
    if (!lastGeneratedInteriorPdf) return;
    try {
      await fetch(`/api/open-folder?path=${encodeURIComponent(lastGeneratedInteriorPdf)}`);
    } catch (e) {
      console.error(e);
    }
  });

  resultFilePath.addEventListener('click', async () => {
    if (!lastGeneratedInteriorPdf) return;
    try {
      await fetch(`/api/open-folder?path=${encodeURIComponent(lastGeneratedInteriorPdf)}`);
    } catch (e) {
      console.error(e);
    }
  });

  // ==========================================
  // Cover Builder Logic
  // ==========================================
  async function loadCoverDetails() {
    const folder = inputFolder.value.trim();
    if (!folder) return;

    const format = getSelectedFormat();

    try {
      const res = await fetch(`/api/cover-details?folder_path=${encodeURIComponent(folder)}&format=${format}`);
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Не удалось получить данные обложки');
      }

      const data = await res.json();
      currentCoverDetails = data;
      renderCoverDetails(data);
    } catch (err) {
      console.warn('Cover details error:', err.message);
    }
  }

  function renderCoverDetails(data) {
    // 1. Status indicators
    if (data.has_front) {
      frontDot.className = 'status-indicator-dot dot-found';
      frontCoverFilename.textContent = `✓ ${data.front_cover_name}`;
    } else {
      frontDot.className = 'status-indicator-dot dot-missing';
      frontCoverFilename.textContent = 'cover_front.* не найден';
    }

    if (data.has_back) {
      backDot.className = 'status-indicator-dot dot-found';
      backCoverFilename.textContent = `✓ ${data.back_cover_name}`;
    } else {
      backDot.className = 'status-indicator-dot dot-missing';
      backCoverFilename.textContent = 'cover_back.* не найден';
    }

    if (data.has_both_covers) {
      coverStatusTip.innerHTML = `<span style="color: #6ee7b7;">✓ Обе обложки обнаружены и готовы к сборке.</span>`;
    } else {
      coverStatusTip.innerHTML = `Поместите файлы <code>cover_front.png</code> и <code>cover_back.png</code> в выбранную папку книги.`;
    }

    // 2. Spine calculation
    inputSpineWidth.value = data.recommended_spine_mm;
    spinePagesNote.textContent = `По расчёту Amazon KDP: ${data.total_interior_pages} стр. блока (${data.recommended_spine_mm} мм)`;

    // 3. Setup default thumbnails if empty
    if (!selectedThumbnails[0] && data.default_thumbnails && data.default_thumbnails.length > 0) {
      selectedThumbnails = [
        data.default_thumbnails[0] || null,
        data.default_thumbnails[1] || null,
        data.default_thumbnails[2] || null,
        data.default_thumbnails[3] || null
      ];
    }
    renderChosenThumbSlots();

    // 4. Populate drawer gallery
    renderDrawerGallery(data.interior_images || []);
  }

  btnRecalcSpine.addEventListener('click', () => {
    if (currentCoverDetails && currentCoverDetails.recommended_spine_mm) {
      inputSpineWidth.value = currentCoverDetails.recommended_spine_mm;
    }
  });

  // Spine Color Synchronizations
  inputSpineColor.addEventListener('input', (e) => {
    inputSpineColorHex.value = e.target.value.toUpperCase();
  });

  inputSpineColorHex.addEventListener('input', (e) => {
    let val = e.target.value.trim();
    if (!val.startsWith('#')) val = '#' + val;
    if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
      inputSpineColor.value = val;
    }
  });

  colorSwatches.forEach(swatch => {
    swatch.addEventListener('click', () => {
      const color = swatch.dataset.color;
      inputSpineColor.value = color;
      inputSpineColorHex.value = color.toUpperCase();
    });
  });

  // Chosen Thumb Slots
  function renderChosenThumbSlots() {
    const slots = chosenThumbsGrid.querySelectorAll('.thumb-slot');
    let filledCount = 0;

    slots.forEach((slot, idx) => {
      const imgPath = selectedThumbnails[idx];
      slot.classList.toggle('active-slot', idx === activeSlotIndex);

      if (imgPath) {
        filledCount++;
        slot.innerHTML = `
          <img src="/api/image?path=${encodeURIComponent(imgPath)}" alt="Thumb ${idx + 1}">
          <span class="slot-badge-num">${idx + 1}</span>
        `;
      } else {
        slot.innerHTML = `
          <span class="slot-empty">${idx + 1}</span>
        `;
      }

      slot.onclick = () => {
        activeSlotIndex = idx;
        activeSlotHint.textContent = `Выбор для слота ${idx + 1}`;
        interiorGalleryDrawer.classList.remove('hidden');
        renderChosenThumbSlots();
      };
    });

    thumbsCountBadge.textContent = `${filledCount} выбрано`;
  }

  btnToggleGallery.addEventListener('click', () => {
    interiorGalleryDrawer.classList.toggle('hidden');
  });

  function renderDrawerGallery(images) {
    interiorGalleryGrid.innerHTML = '';
    if (!images || images.length === 0) {
      interiorGalleryGrid.innerHTML = `<div style="grid-column: 1/-1; font-size: 11px; color: var(--text-dim); text-align: center; padding: 16px;">Нет доступных иллюстраций interior</div>`;
      return;
    }

    images.forEach(item => {
      const div = document.createElement('div');
      div.className = 'drawer-thumb-item';
      div.title = item.name;
      div.innerHTML = `<img src="${item.preview_url}" alt="${item.name}" loading="lazy">`;

      div.onclick = () => {
        selectedThumbnails[activeSlotIndex] = item.path;
        activeSlotIndex = (activeSlotIndex + 1) % 4;
        activeSlotHint.textContent = `Выбор для слота ${activeSlotIndex + 1}`;
        renderChosenThumbSlots();
      };

      interiorGalleryGrid.appendChild(div);
    });
  }

  // ==========================================
  // Preview Cover (Rendered on Button Click)
  // ==========================================
  btnPreviewCover.addEventListener('click', () => {
    if (!currentCoverDetails) {
      return alert('Данные книги не загружены. Укажите папку книги.');
    }
    if (!currentCoverDetails.front_cover) {
      return alert('Файл cover_front.* не найден в папке книги.');
    }
    if (!currentCoverDetails.back_cover) {
      return alert('Файл cover_back.* не найден в папке книги.');
    }

    renderCoverStagePreview();
  });

  async function renderCoverStagePreview() {
    const format = getSelectedFormat();
    const spineWidthMm = parseFloat(inputSpineWidth.value) || 4.6;
    const spineColor = inputSpineColor.value || '#2d5a27';

    // Fetch unified layout from single source of truth in backend
    let layout = null;
    try {
      const res = await fetch(`/api/cover-layout?format=${format}&spine_width_mm=${spineWidthMm}`);
      if (res.ok) {
        layout = await res.json();
      }
    } catch (e) {
      console.warn('Could not fetch cover layout:', e);
    }

    if (!layout && currentCoverDetails && currentCoverDetails.layout) {
      layout = currentCoverDetails.layout;
    }

    if (!layout) return;

    coverDimsBadge.textContent = `${layout.total_width_mm} × ${layout.total_height_mm} мм (с Bleed ${layout.bleed_mm}мм)`;

    // Scale calculation to fit inside canvas container
    const containerW = Math.min(860, coverCanvasContainer.clientWidth - 48);
    const scale = containerW / layout.total_width_pt;

    const stageWidthPx = containerW;
    const stageHeightPx = layout.total_height_pt * scale;

    coverStage.style.width = `${stageWidthPx}px`;
    coverStage.style.height = `${stageHeightPx}px`;

    // 1. Back Cover (Exact proportional width)
    coverBackPane.style.flex = `0 0 ${layout.panes.back_pct}%`;
    coverBackPane.style.width = `${layout.panes.back_pct}%`;
    coverBackPane.style.backgroundImage = `url('/api/image?path=${encodeURIComponent(currentCoverDetails.back_cover)}')`;

    // 2. Spine (Exact proportional width without distortion)
    coverSpinePane.style.flex = `0 0 ${layout.panes.spine_pct}%`;
    coverSpinePane.style.width = `${layout.panes.spine_pct}%`;
    coverSpinePane.style.backgroundColor = spineColor;

    // 3. Front Cover (Exact proportional width)
    coverFrontPane.style.flex = `0 0 ${layout.panes.front_pct}%`;
    coverFrontPane.style.width = `${layout.panes.front_pct}%`;
    coverFrontPane.style.backgroundImage = `url('/api/image?path=${encodeURIComponent(currentCoverDetails.front_cover)}')`;

    // 4. Position Thumbnails Grid using exact unified percentage geometry
    const coverThumbsQuad = document.getElementById('coverThumbsQuad');
    if (coverThumbsQuad && layout.grid) {
      coverThumbsQuad.style.left = `${layout.grid.left_pct}%`;
      coverThumbsQuad.style.top = `${layout.grid.top_pct}%`;
      coverThumbsQuad.style.width = `${layout.grid.width_pct}%`;
      coverThumbsQuad.style.height = `${layout.grid.height_pct}%`;
      const gapPx = Math.max(4, layout.grid.gap_x_pt * scale);
      coverThumbsQuad.style.gap = `${gapPx}px`;
    }

    // 5. Position Brand Logo using exact unified percentage geometry
    const logoArea = document.querySelector('.cover-brand-logo-area');
    if (logoArea && layout.logo) {
      logoArea.style.left = `${layout.logo.left_pct}%`;
      logoArea.style.bottom = `${layout.logo.bottom_pct}%`;
      logoArea.style.width = `${layout.logo.width_pct}%`;
    }

    // 6. Update the 4 preview images on back cover
    for (let i = 0; i < 4; i++) {
      const imgPath = selectedThumbnails[i];
      const card = document.getElementById(`ctCard${i}`);
      const img = document.getElementById(`ctImg${i}`);
      if (imgPath) {
        img.src = `/api/image?path=${encodeURIComponent(imgPath)}`;
        card.style.display = 'block';
      } else {
        card.style.display = 'none';
      }
    }

    coverEmptyState.style.display = 'none';
    coverStage.classList.remove('hidden');
  }

  // ==========================================
  // Build Cover PDF
  // ==========================================
  btnBuildCover.addEventListener('click', async () => {
    const folder = inputFolder.value.trim();
    if (!folder) return alert('Укажите папку книги');

    if (!currentCoverDetails || !currentCoverDetails.has_both_covers) {
      return alert('В папке книги должны присутствовать файлы cover_front.* и cover_back.*');
    }

    btnBuildCover.disabled = true;
    btnBuildCoverText.textContent = 'Сборка Cover PDF...';

    const validThumbs = selectedThumbnails.filter(t => t && t.length > 0);
    const spineWidthMm = parseFloat(inputSpineWidth.value) || 4.6;
    const spineColor = inputSpineColor.value || '#2d5a27';

    try {
      const res = await fetch('/api/build-cover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder_path: folder,
          format: getSelectedFormat(),
          front_cover_path: currentCoverDetails.front_cover,
          back_cover_path: currentCoverDetails.back_cover,
          interior_image_paths: validThumbs,
          spine_width_mm: spineWidthMm,
          spine_color: spineColor
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Ошибка сборки Cover PDF');

      lastGeneratedCoverPdf = data.output_path;
      coverResultFilePath.textContent = data.file_name;
      coverResultSize.textContent = `${data.size_mb} MB`;
      coverResultFormat.textContent = data.format.toUpperCase();
      btnCoverDownload.href = `/api/download?path=${encodeURIComponent(data.output_path)}`;
      coverResultBox.classList.remove('hidden');
    } catch (err) {
      alert(`Ошибка: ${err.message}`);
    } finally {
      btnBuildCover.disabled = false;
      btnBuildCoverText.textContent = 'Собрать Cover PDF для Amazon KDP';
    }
  });

  btnCoverOpenFolder.addEventListener('click', async () => {
    if (!lastGeneratedCoverPdf) return;
    try {
      await fetch(`/api/open-folder?path=${encodeURIComponent(lastGeneratedCoverPdf)}`);
    } catch (e) {
      console.error(e);
    }
  });

  coverResultFilePath.addEventListener('click', async () => {
    if (!lastGeneratedCoverPdf) return;
    try {
      await fetch(`/api/open-folder?path=${encodeURIComponent(lastGeneratedCoverPdf)}`);
    } catch (e) {
      console.error(e);
    }
  });

  // ==========================================
  // A+ Content Logic
  // ==========================================

  let aplusInitialized = false;

  async function initAplusTab() {
    if (!aplusInitialized) {
      setupAplusEventHandlers();
      aplusInitialized = true;
    }
    if (!aplusTemplates || aplusTemplates.length === 0) {
      await loadAplusTemplates();
    }
    syncAplusWithCurrentBook();
  }

  async function loadAplusTemplates(customDir = null) {
    try {
      let url = '/api/aplus/templates';
      if (customDir) {
        url += `?templates_dir=${encodeURIComponent(customDir)}`;
      }
      const res = await fetch(url);
      if (!res.ok) throw new Error('Не удалось загрузить список шаблонов');
      const data = await res.json();
      aplusTemplates = data.templates || [];
      if (aplusTemplatesFolderHint) {
        aplusTemplatesFolderHint.textContent = data.templates_dir || '';
      }
      if (aplusTemplatesCount) {
        aplusTemplatesCount.textContent = `${aplusTemplates.length} шаблонов`;
      }

      renderAplusTemplates();

      // Auto-select template matching book format if none selected yet
      if (!selectedAplusTemplate && aplusTemplates.length > 0) {
        const currentFmt = getSelectedFormat();
        const match = aplusTemplates.find(t => t.format === currentFmt) || aplusTemplates[0];
        selectAplusTemplate(match);
      }
    } catch (err) {
      console.error('Error loading A+ templates:', err);
    }
  }

  function renderAplusTemplates() {
    if (!aplusTemplatesGrid) return;
    aplusTemplatesGrid.innerHTML = '';
    const filtered = aplusTemplates.filter(t => {
      if (aplusFilter === 'all') return true;
      return t.format === aplusFilter;
    });

    if (filtered.length === 0) {
      aplusTemplatesGrid.innerHTML = `<div style="grid-column: 1/-1; padding: 20px; text-align: center; color: var(--text-dim); font-size: 12px;">Нет шаблонов в выбранной категории</div>`;
      return;
    }

    filtered.forEach(t => {
      const card = document.createElement('div');
      card.className = `aplus-template-card ${selectedAplusTemplate && selectedAplusTemplate.filename === t.filename ? 'active' : ''}`;
      const fmtLabel = t.format === 'a4' ? 'A4' : 'Square 8.5"';
      card.innerHTML = `
        <div class="template-card-preview">
          <img src="/api/image?path=${encodeURIComponent(t.path)}" alt="${t.title}" loading="lazy">
          <span class="template-card-badge">${fmtLabel}</span>
        </div>
        <div class="template-card-info">
          <div class="template-card-title" title="${t.title}">${t.title}</div>
          <div class="template-card-sub">${t.slots_count} слота • ${t.width}×${t.height}</div>
        </div>
      `;
      card.addEventListener('click', () => {
        selectAplusTemplate(t);
      });
      aplusTemplatesGrid.appendChild(card);
    });
  }

  function selectAplusTemplate(tmpl) {
    selectedAplusTemplate = tmpl;
    // Highlight active card in grid
    document.querySelectorAll('.aplus-template-card').forEach(c => {
      c.classList.remove('active');
    });
    const cards = aplusTemplatesGrid.querySelectorAll('.aplus-template-card');
    cards.forEach(c => {
      if (c.querySelector('.template-card-title')?.textContent === tmpl.title) {
        c.classList.add('active');
      }
    });

    if (aplusDimsBadge) {
      aplusDimsBadge.textContent = `${tmpl.width} × ${tmpl.height} px • ${tmpl.slots_count} слота`;
    }
    if (aplusSlotsBadge) {
      aplusSlotsBadge.textContent = `${tmpl.slots_count} слота`;
    }

    // Trigger preview
    triggerAplusPreview();
  }

  function syncAplusWithCurrentBook() {
    renderAplusGallery();

    // If slots are completely empty, auto-populate with first 4 illustrations
    const hasAny = aplusSelectedImages.some(img => img !== null);
    if (!hasAny) {
      autoSelectAplusImages('first');
    } else {
      updateAplusSlotsUI();
      triggerAplusPreview();
    }
  }

  function getAvailableInteriorImages() {
    if (currentCoverDetails && currentCoverDetails.interior_images && currentCoverDetails.interior_images.length > 0) {
      return currentCoverDetails.interior_images;
    }
    if (currentPlan && currentPlan.pages) {
      return currentPlan.pages
        .filter(p => !p.is_blank && p.image_path)
        .map(p => ({
          name: p.image_name,
          path: p.image_path,
          preview_url: `/api/image?path=${encodeURIComponent(p.image_path)}`
        }));
    }
    return [];
  }

  function renderAplusGallery() {
    if (!aplusGalleryGrid) return;
    const images = getAvailableInteriorImages();
    aplusGalleryGrid.innerHTML = '';

    if (images.length === 0) {
      aplusGalleryGrid.innerHTML = `<div style="grid-column: 1/-1; padding: 12px; text-align: center; color: var(--text-dim); font-size: 11px;">Нет изображений в выбранной папке книги</div>`;
      return;
    }

    images.forEach(img => {
      const item = document.createElement('div');
      const inSlot = aplusSelectedImages.includes(img.path);
      item.className = `aplus-gallery-item ${inSlot ? 'in-slot' : ''}`;
      item.title = `Поместить ${img.name} в активный слот`;
      item.innerHTML = `<img src="${img.preview_url}" alt="${img.name}" loading="lazy">`;
      item.addEventListener('click', () => {
        assignImageToActiveSlot(img.path, img.name);
      });
      aplusGalleryGrid.appendChild(item);
    });
  }

  function updateAplusSlotsUI() {
    if (!aplusSlotsGrid) return;
    const images = getAvailableInteriorImages();
    for (let i = 0; i < 4; i++) {
      const slotCard = aplusSlotsGrid.querySelector(`[data-slot="${i}"]`);
      const thumb = document.getElementById(`aplusSlotThumb${i}`);
      const nameEl = document.getElementById(`aplusSlotName${i}`);

      if (slotCard) {
        slotCard.classList.toggle('active', i === aplusActiveSlot);
      }

      const imgPath = aplusSelectedImages[i];
      if (imgPath && thumb && nameEl) {
        const found = images.find(img => img.path === imgPath);
        const fileName = found ? found.name : imgPath.split(/[\\/]/).pop();
        thumb.innerHTML = `<img src="/api/image?path=${encodeURIComponent(imgPath)}" alt="${fileName}">`;
        nameEl.textContent = fileName;
      } else if (thumb && nameEl) {
        thumb.innerHTML = `<span class="slot-placeholder">Слот ${i + 1}</span>`;
        nameEl.textContent = '—';
      }
    }

    if (aplusDrawerTitle) {
      aplusDrawerTitle.textContent = `Кликните по иллюстрации книги, чтобы поместить в Слот ${aplusActiveSlot + 1}:`;
    }
    renderAplusGallery();
  }

  function assignImageToActiveSlot(path, name) {
    aplusSelectedImages[aplusActiveSlot] = path;
    // Advance to next slot
    aplusActiveSlot = (aplusActiveSlot + 1) % 4;
    updateAplusSlotsUI();
    triggerAplusPreview();
  }

  function autoSelectAplusImages(mode = 'first') {
    const images = getAvailableInteriorImages();
    if (images.length === 0) return;

    if (mode === 'random') {
      const shuffled = [...images].sort(() => 0.5 - Math.random());
      for (let i = 0; i < 4; i++) {
        aplusSelectedImages[i] = shuffled[i] ? shuffled[i].path : null;
      }
    } else {
      for (let i = 0; i < 4; i++) {
        aplusSelectedImages[i] = images[i] ? images[i].path : null;
      }
    }
    updateAplusSlotsUI();
    triggerAplusPreview();
  }

  let previewDebounceTimer = null;
  function triggerAplusPreview() {
    clearTimeout(previewDebounceTimer);
    previewDebounceTimer = setTimeout(fetchAplusPreview, 250);
  }

  async function fetchAplusPreview() {
    if (!selectedAplusTemplate) return;
    const validImages = aplusSelectedImages.filter(Boolean);
    if (validImages.length === 0) {
      if (aplusEmptyState) aplusEmptyState.classList.remove('hidden');
      if (aplusPreviewStage) aplusPreviewStage.classList.add('hidden');
      return;
    }

    const fitMode = document.querySelector('input[name="aplusFitMode"]:checked')?.value || 'contain';

    try {
      if (aplusPreviewImg) aplusPreviewImg.style.opacity = '0.5';
      const res = await fetch('/api/aplus/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_path: selectedAplusTemplate.path,
          image_paths: aplusSelectedImages,
          fit_mode: fitMode
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка предпросмотра');
      }

      const data = await res.json();
      if (aplusPreviewImg) {
        aplusPreviewImg.src = data.preview_url;
        aplusPreviewImg.style.opacity = '1';
      }
      if (aplusEmptyState) aplusEmptyState.classList.add('hidden');
      if (aplusPreviewStage) aplusPreviewStage.classList.remove('hidden');
    } catch (e) {
      console.error('Preview error:', e);
    } finally {
      if (aplusPreviewImg) aplusPreviewImg.style.opacity = '1';
    }
  }

  function setupAplusEventHandlers() {
    // Browse templates folder
    if (btnBrowseAplusFolder) {
      btnBrowseAplusFolder.addEventListener('click', async () => {
        btnBrowseAplusFolder.disabled = true;
        try {
          const res = await fetch('/api/aplus/browse-templates-folder');
          if (res.ok) {
            const data = await res.json();
            if (!data.cancelled && data.path) {
              aplusCustomFolder = data.path;
              await loadAplusTemplates(data.path);
            }
          }
        } catch (e) {
          console.error(e);
        } finally {
          btnBrowseAplusFolder.disabled = false;
        }
      });
    }

    // Filter pills
    if (aplusFilterPills) {
      aplusFilterPills.querySelectorAll('.filter-pill').forEach(btn => {
        btn.addEventListener('click', () => {
          aplusFilterPills.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          aplusFilter = btn.dataset.filter;
          renderAplusTemplates();
        });
      });
    }

    // Slots click to switch active slot
    if (aplusSlotsGrid) {
      aplusSlotsGrid.querySelectorAll('.aplus-slot-card').forEach(card => {
        card.addEventListener('click', () => {
          const slotIdx = parseInt(card.dataset.slot, 10);
          aplusActiveSlot = slotIdx;
          updateAplusSlotsUI();
        });
      });
    }

    // Buttons Auto & Random
    if (btnAplusAutoSelect) {
      btnAplusAutoSelect.addEventListener('click', () => autoSelectAplusImages('first'));
    }
    if (btnAplusRandomSelect) {
      btnAplusRandomSelect.addEventListener('click', () => autoSelectAplusImages('random'));
    }

    // Fit mode chips
    if (chipFitContain && chipFitCover) {
      [chipFitContain, chipFitCover].forEach(chip => {
        chip.addEventListener('click', () => {
          chipFitContain.classList.remove('active');
          chipFitCover.classList.remove('active');
          chip.classList.add('active');
          const radio = chip.querySelector('input');
          if (radio) radio.checked = true;
          triggerAplusPreview();
        });
      });
    }

    // Preview button
    if (btnAplusPreview) {
      btnAplusPreview.addEventListener('click', fetchAplusPreview);
    }

    // Build button
    if (btnAplusBuild) {
      btnAplusBuild.addEventListener('click', buildAplusBanner);
    }

    // Open folder in result box
    if (btnAplusOpenFolder) {
      btnAplusOpenFolder.addEventListener('click', async () => {
        const folder = inputFolder.value.trim();
        if (!folder) return;
        try {
          const target = (lastGeneratedAplusFiles && lastGeneratedAplusFiles.length > 0)
            ? lastGeneratedAplusFiles[0].path
            : folder;
          await fetch(`/api/open-folder?path=${encodeURIComponent(target)}`);
        } catch (e) {
          console.error(e);
        }
      });
    }
  }

  async function buildAplusBanner() {
    const folder = inputFolder.value.trim();
    if (!folder) {
      alert('Пожалуйста, выберите папку книги в верхней панели');
      return;
    }
    if (!selectedAplusTemplate) {
      alert('Пожалуйста, выберите шаблон баннера');
      return;
    }

    const validImages = aplusSelectedImages.filter(Boolean);
    if (validImages.length === 0) {
      alert('Пожалуйста, выберите хотя бы одну картинку для баннера');
      return;
    }

    btnAplusBuild.disabled = true;
    btnAplusBuildText.textContent = '⏳ Сборка A+ баннера...';

    const fitMode = document.querySelector('input[name="aplusFitMode"]:checked')?.value || 'contain';
    const customName = aplusCustomName ? aplusCustomName.value.trim() : null;
    const exportAmazon = chkAplusExportAmazon ? chkAplusExportAmazon.checked : true;

    try {
      const res = await fetch('/api/aplus/build', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder_path: folder,
          template_path: selectedAplusTemplate.path,
          image_paths: aplusSelectedImages,
          custom_output_name: customName || null,
          export_amazon_size: exportAmazon,
          fit_mode: fitMode
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Не удалось сгенерировать баннер');
      }

      const result = await res.json();
      lastGeneratedAplusFiles = result.files || [];

      // Render Result Card
      if (aplusResultFolder) {
        aplusResultFolder.textContent = `Сохранено в: ${result.output_folder}`;
      }
      if (aplusFilesList) {
        aplusFilesList.innerHTML = '';
        lastGeneratedAplusFiles.forEach(file => {
          const row = document.createElement('div');
          row.className = 'aplus-file-item';
          row.innerHTML = `
            <div class="aplus-file-info">
              <span class="aplus-file-name">📄 ${file.filename}</span>
              <span class="aplus-file-meta">${file.width} × ${file.height} px • ${file.size_kb} KB</span>
            </div>
            <span class="aplus-file-badge">${file.type}</span>
          `;
          aplusFilesList.appendChild(row);
        });
      }

      if (aplusResultBox) {
        aplusResultBox.classList.remove('hidden');
        aplusResultBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    } catch (err) {
      console.error(err);
      alert(`Ошибка генерации баннера: ${err.message}`);
    } finally {
      btnAplusBuild.disabled = false;
      btnAplusBuildText.textContent = '✨ Сгенерировать A+ Баннер в папку книги';
    }
  }

  // ==========================================
  // Auto-restore last folder from localStorage
  // ==========================================
  try {
    const savedFolder = localStorage.getItem('kdp_last_folder');
    if (savedFolder) {
      inputFolder.value = savedFolder;
      syncProject();
    }
  } catch (e) {}

  // Initialize A+ handlers & preload templates immediately
  try {
    setupAplusEventHandlers();
    loadAplusTemplates();
  } catch (e) {
    console.error('Error preloading A+ templates:', e);
  }
});
