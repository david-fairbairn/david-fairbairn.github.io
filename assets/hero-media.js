(() => {
  const hero = document.querySelector('.hero-banner');
  if (!hero) return;

  const media = hero.querySelector('.hero-media');
  const toggle = hero.querySelector('.hero-motion-toggle');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const interval = Math.max(3000, Number(hero.dataset.heroInterval) || 6000);
  let slides = [];
  let current = 0;
  let timer;
  let video;
  let videoReady = false;
  let paused = reducedMotion.matches;

  const update = () => {
    clearInterval(timer);
    const running = !paused && !document.hidden;
    toggle.hidden = !videoReady && slides.length < 2;
    toggle.textContent = paused ? 'Play background' : 'Pause background';
    if (videoReady) {
      if (running) {
        video.play().catch(() => {
          paused = true;
          update();
        });
      } else {
        video.pause();
      }
    } else if (running && slides.length > 1) {
      timer = setInterval(() => {
        slides[current].classList.remove('is-active');
        current = (current + 1) % slides.length;
        slides[current].classList.add('is-active');
      }, interval);
    }
  };

  toggle.addEventListener('click', () => {
    paused = !paused;
    update();
  });
  document.addEventListener('visibilitychange', update);
  reducedMotion.addEventListener('change', () => {
    paused = reducedMotion.matches;
    update();
  });

  let imageUrls = [];
  try {
    const configured = JSON.parse(hero.dataset.heroImages || '[]');
    if (Array.isArray(configured)) {
      imageUrls = configured.filter(url => typeof url === 'string' && url.trim());
    }
  } catch {
    // Keep the decorative fallback when the image configuration is invalid.
  }
  const poster = hero.dataset.heroPoster.trim();
  if (poster) imageUrls.unshift(poster);
  imageUrls = [...new Set(imageUrls)];

  const loadImage = url => new Promise(resolve => {
    const image = new Image();
    image.alt = '';
    image.className = 'hero-slide';
    image.decoding = 'async';
    image.onload = () => resolve(image);
    image.onerror = () => resolve(null);
    image.src = url;
  });

  // Show the first usable image immediately; preserve configured slide order.
  const pending = imageUrls.map(url => loadImage(url).then(image => {
    if (image && !media.querySelector('.hero-slide')) {
      image.classList.add('is-active');
      media.append(image);
    }
    return image;
  }));
  Promise.all(pending).then(images => {
    slides = images.filter(Boolean);
    const active = slides.findIndex(image => image.classList.contains('is-active'));
    current = Math.max(0, active);
    slides.forEach(image => media.append(image));
    update();
  });

  const videoUrl = hero.dataset.heroVideo.trim();
  if (videoUrl) {
    video = document.createElement('video');
    video.className = 'hero-video';
    video.muted = true;
    video.defaultMuted = true;
    video.loop = true;
    video.playsInline = true;
    video.preload = 'auto';
    video.setAttribute('muted', '');
    video.setAttribute('playsinline', '');
    if (poster) video.poster = poster;
    video.addEventListener('loadeddata', () => {
      videoReady = true;
      video.classList.add('is-ready');
      update();
    });
    video.addEventListener('error', () => {
      videoReady = false;
      video.classList.remove('is-ready');
      update();
    });
    media.append(video);
    video.src = videoUrl;
  }
})();
