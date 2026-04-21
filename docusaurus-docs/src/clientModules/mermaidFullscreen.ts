import ExecutionEnvironment from '@docusaurus/ExecutionEnvironment';

const BUTTON_CLASS = 'mermaid-fullscreen-btn';
const BUTTON_LABEL = 'Fullscreen';
const EXIT_LABEL = 'Exit';

const ENTER_ICON = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h6v2H6v4H4V4zm10 0h6v6h-2V6h-4V4zM4 14h2v4h4v2H4v-6zm14 0h2v6h-6v-2h4v-4z"/></svg>`;
const EXIT_ICON = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 4h2v4h4v2H6V4zm10 0h2v6h-6V8h4V4zM4 14h6v6H8v-4H4v-2zm10 0h6v2h-4v4h-2v-6z"/></svg>`;

function requestFs(el: HTMLElement): Promise<void> {
  const fn =
    (el as any).requestFullscreen ||
    (el as any).webkitRequestFullscreen ||
    (el as any).msRequestFullscreen;
  return fn ? fn.call(el) : Promise.reject();
}

function exitFs(): Promise<void> {
  const fn =
    (document as any).exitFullscreen ||
    (document as any).webkitExitFullscreen ||
    (document as any).msExitFullscreen;
  return fn ? fn.call(document) : Promise.reject();
}

function currentFsElement(): Element | null {
  return (
    document.fullscreenElement ||
    (document as any).webkitFullscreenElement ||
    (document as any).msFullscreenElement ||
    null
  );
}

function renderButton(btn: HTMLButtonElement, isFullscreen: boolean) {
  btn.innerHTML = `${isFullscreen ? EXIT_ICON : ENTER_ICON}<span>${
    isFullscreen ? EXIT_LABEL : BUTTON_LABEL
  }</span>`;
}

function attachButton(container: HTMLElement) {
  if (container.querySelector(`.${BUTTON_CLASS}`)) return;

  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = BUTTON_CLASS;
  btn.setAttribute('aria-label', 'Toggle fullscreen diagram');
  renderButton(btn, false);

  btn.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (currentFsElement() === container) {
      exitFs().catch(() => {});
    } else {
      requestFs(container).catch(() => {});
    }
  });

  container.appendChild(btn);
}

function scanAndAttach() {
  document
    .querySelectorAll<HTMLElement>('.docusaurus-mermaid-container')
    .forEach(attachButton);
}

if (ExecutionEnvironment.canUseDOM) {
  const onReady = () => {
    scanAndAttach();

    const observer = new MutationObserver(() => scanAndAttach());
    observer.observe(document.body, {childList: true, subtree: true});

    const syncButtons = () => {
      const fsEl = currentFsElement();
      document
        .querySelectorAll<HTMLElement>('.docusaurus-mermaid-container')
        .forEach((container) => {
          const btn = container.querySelector<HTMLButtonElement>(
            `.${BUTTON_CLASS}`,
          );
          if (!btn) return;
          renderButton(btn, fsEl === container);
        });
    };

    document.addEventListener('fullscreenchange', syncButtons);
    document.addEventListener('webkitfullscreenchange', syncButtons);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', onReady);
  } else {
    onReady();
  }
}

export {};
