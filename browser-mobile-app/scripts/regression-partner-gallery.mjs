import { readFileSync } from 'node:fs';

const page = readFileSync(new URL('../src/pages/PartnerPage.tsx', import.meta.url), 'utf8');
const styles = readFileSync(new URL('../src/styles.css', import.meta.url), 'utf8');

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const lastLightboxBlock = styles.slice(styles.lastIndexOf('/* Fullscreen partner image viewer'));

assert(page.includes('createPortal(gallery, document.body)'), 'partner gallery must render through a React portal into document.body');
assert(lastLightboxBlock.includes('position: fixed') && lastLightboxBlock.includes('inset: 0'), 'lightbox overlay must be fixed and cover the viewport with inset: 0');
assert(/\.lightbox[^}]*z-index:\s*99999/s.test(lastLightboxBlock), 'lightbox z-index must stay above bottom navigation');
assert(/\.lightbox__image[\s\S]*object-fit:\s*contain/s.test(lastLightboxBlock), 'lightbox image must use object-fit: contain');
assert(page.includes('document.body.style.overflow = "hidden"') && page.includes('document.body.style.overflow = previousOverflow'), 'body scroll lock must be applied and restored');
assert(!/body\.style\.position\s*=\s*"fixed"/.test(page), 'gallery scroll lock must not fix body position and cause page jumps');
assert(/\.bottom-nav[\s\S]*z-index:\s*(?:[0-9]{1,4}|9999)\b/.test(styles), 'bottom nav z-index should remain lower than the fullscreen overlay');
assert(!/createPortal\([^)]*bottom-nav/i.test(page), 'bottom navigation must not be rendered into the gallery portal');

console.log('Partner gallery static regression checks passed.');
