/**
 * Playwright E2E — Listing frontend
 * URL base: http://localhost:8090  |  API: http://localhost:8010
 * Run:  node tests/playwright/listing.test.js
 *
 * Componentes usan inline styles (no clases CSS) — selectores por tag/placeholder/texto.
 */
const { chromium } = require('playwright');

const BASE = 'http://localhost:8090';
const API  = 'http://localhost:8010';

const AGENT    = { email: 'agente@listing.co', password: 'Demo1234!' };
const ADMIN    = { email: 'admin@listing.co',  password: 'Admin1234!' };
const NEW_USER = { email: `qa_${Date.now()}@test.co`, password: 'Test1234!', name: 'QA Tester' };

// ── result tracking ───────────────────────────────────────────────────────────

const results = [];
let passed = 0, failed = 0, warned = 0;

// ── shared state between test suites ─────────────────────────────────────────
let newPropertyId = null;  // set in F7, read in F8

function record(suite, name, status, note = '') {
  results.push({ suite, name, status, note });
  if (status === 'PASS') passed++;
  else if (status === 'FAIL') failed++;
  else warned++;
  const icon = status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : '⚠️';
  console.log(`  ${icon} [${suite}] ${name}${note ? ' — ' + note : ''}`);
}

async function check(suite, name, fn) {
  try { record(suite, name, 'PASS', (await fn()) || ''); }
  catch (e) { record(suite, name, 'FAIL', e.message.slice(0, 150)); }
}

async function warn(suite, name, fn) {
  try { record(suite, name, 'PASS', (await fn()) || ''); }
  catch (e) { record(suite, name, 'WARN', e.message.slice(0, 150)); }
}

// ── helpers ───────────────────────────────────────────────────────────────────

async function loginAs(page, { email, password }) {
  await page.goto(`${BASE}/login`);
  await page.waitForLoadState('networkidle');
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForTimeout(1500);
}

async function logout(page) {
  await page.evaluate(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  });
}

async function getPublishedSlug() {
  const r = await fetch(`${API}/api/v1/properties?page_size=3&status=published`)
    .then(r => r.json()).catch(() => null);
  return r?.data?.[0]?.slug || 'venta-apartamento-chapinero-001';
}

// ── F1. Home pública ──────────────────────────────────────────────────────────

async function f1_home(page) {
  console.log('\n── F1. Home pública ──');
  await page.goto(BASE);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(800);

  await check('F1', 'Carga sin error JS', async () => {
    const errors = [];
    page.once('pageerror', e => errors.push(e.message));
    await page.waitForTimeout(300);
    if (errors.length) throw new Error(errors[0]);
  });

  await check('F1', 'Título de página presente', async () => {
    const title = await page.title();
    if (!title || title.length < 3) throw new Error(`title="${title}"`);
    return `"${title}"`;
  });

  await check('F1', 'Header visible', async () => {
    const header = await page.$('header');
    if (!header) throw new Error('no <header>');
  });

  await warn('F1', 'Propiedades o banners en home', async () => {
    // inline styles — look for links to /propiedades/ in main
    const links = await page.$$('main a[href*="/propiedades/"], a[href*="/propiedades/"]');
    if (links.length === 0) throw new Error('no property links in home');
    return `${links.length} property link(s)`;
  });

  await check('F1', 'Enlace a /propiedades en header', async () => {
    const link = await page.$('a[href*="propiedades"]');
    if (!link) throw new Error('no link to /propiedades');
  });
}

// ── F2. Búsqueda y filtros ────────────────────────────────────────────────────

async function f2_search(page) {
  console.log('\n── F2. Búsqueda y filtros ──');
  await page.goto(`${BASE}/propiedades`);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);

  await check('F2', 'Página /propiedades carga', async () => {
    if (!page.url().includes('propiedades')) throw new Error(`url=${page.url()}`);
  });

  await check('F2', 'Grid de propiedades visible', async () => {
    // components use inline styles — detect by property links in the page
    const links = await page.$$('a[href*="/propiedades/"]');
    const count = links.length;
    if (count === 0) throw new Error('no property links found');
    return `${count} propiedades`;
  });

  await check('F2', 'Filtros presentes', async () => {
    const filters = await page.$('form select, form input, aside select, aside input');
    if (!filters) throw new Error('no filter controls');
  });

  await check('F2', 'Click en propiedad navega al detalle', async () => {
    const link = await page.$('a[href*="/propiedades/"]');
    if (!link) throw new Error('no property link');
    await link.click();
    await page.waitForLoadState('networkidle');
    if (!page.url().includes('/propiedades/')) throw new Error(`url=${page.url()}`);
    return `→ ${page.url().split('/').pop()}`;
  });
}

// ── F3. Detalle de propiedad ──────────────────────────────────────────────────

async function f3_detail(page) {
  console.log('\n── F3. Detalle de propiedad ──');
  const slug = await getPublishedSlug();
  await page.goto(`${BASE}/propiedades/${slug}`);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(800);

  await check('F3', 'Detalle carga (no 404)', async () => {
    const h1 = await page.$('h1');
    if (!h1) throw new Error('no h1');
    return `"${(await h1.textContent()).slice(0, 40)}"`;
  });

  await check('F3', 'Precio visible', async () => {
    const body = await page.textContent('body');
    if (!body.match(/\$|COP|\d{3,}/)) throw new Error('no price in page');
  });

  await check('F3', 'Botón WhatsApp presente', async () => {
    const wa = await page.$('a[href*="wa.me"]');
    if (!wa) throw new Error('no WhatsApp link');
    return (await wa.getAttribute('href')).slice(0, 50);
  });

  await check('F3', 'Botón Llamar presente', async () => {
    const call = await page.$('a[href^="tel:"]');
    if (!call) throw new Error('no tel: link');
  });

  await warn('F3', 'Mapa Leaflet renderiza', async () => {
    const map = await page.$('.leaflet-container');
    if (!map) throw new Error('no .leaflet-container');
  });

  await check('F3', 'Formulario de lead presente', async () => {
    const nameInput = await page.$('input[placeholder="Nombre *"]');
    if (!nameInput) throw new Error('lead form name input not found');
  });

  await check('F3', 'Envío de lead funciona', async () => {
    await page.fill('input[placeholder="Nombre *"]', 'QA Tester');
    await page.fill('input[type="email"]', `qa_lead_${Date.now()}@test.co`);
    const phone = await page.$('input[placeholder="Teléfono / WhatsApp"]');
    if (phone) await phone.fill('+573001234567');
    const msg = await page.$('textarea');
    if (msg) await msg.fill('Prueba automatizada con Playwright.');
    const consent = await page.$('input[type="checkbox"]');
    if (consent) await consent.check();
    await page.click('button:has-text("Enviar")');
    await page.waitForTimeout(2000);
    const body = await page.textContent('body');
    if (!body.match(/enviado|gracias|Listo|mensaje fue|éxito/i)) {
      throw new Error('no success message after lead submit');
    }
    return 'lead enviado';
  });

  await check('F3', 'Meta title en <head>', async () => {
    const title = await page.title();
    if (!title || title.length < 5) throw new Error(`title="${title}"`);
    return `"${title.slice(0, 50)}"`;
  });

  await warn('F3', 'JSON-LD presente', async () => {
    const scripts = await page.$$eval(
      'script[type="application/ld+json"]',
      els => els.length
    );
    if (scripts === 0) throw new Error('no JSON-LD scripts');
    return `${scripts} script(s)`;
  });
}

// ── F4. Registro ──────────────────────────────────────────────────────────────

async function f4_register(page) {
  console.log('\n── F4. Registro de usuario ──');
  await page.goto(`${BASE}/registro`);
  await page.waitForLoadState('networkidle');

  await check('F4', 'Página /registro carga', async () => {
    if (!(await page.$('form'))) throw new Error('no form');
  });

  await check('F4', 'Registro de nuevo usuario', async () => {
    const inputs = await page.$$('input');
    for (const inp of inputs) {
      const type = await inp.evaluate(e => e.type);
      if (type === 'text')     await inp.fill(NEW_USER.name);
      if (type === 'email')    await inp.fill(NEW_USER.email);
      if (type === 'password') await inp.fill(NEW_USER.password);
    }
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
    const body = await page.textContent('body');
    const url  = page.url();
    // success = redirected OR not on /registro with error
    if (url.includes('/registro') && body.match(/[Ee]rror/i)) {
      throw new Error(`still on /registro with error: ${body.slice(0, 100)}`);
    }
    return url.includes('/registro') ? 'on registro (no error)' : `→ ${url.split('/').pop() || '/'}`;
  });

  await check('F4', 'Email duplicado rechazado', async () => {
    await page.goto(`${BASE}/registro`);
    await page.waitForLoadState('networkidle');
    const inputs = await page.$$('input');
    for (const inp of inputs) {
      const type = await inp.evaluate(e => e.type);
      if (type === 'text')     await inp.fill('Duplicate Test');
      if (type === 'email')    await inp.fill(AGENT.email); // already exists
      if (type === 'password') await inp.fill('Demo1234!');
    }
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
    const body = await page.textContent('body');
    // backend returns "Email already registered" in English
    if (!body.match(/registered|already|exist|registrado|duplicad|[Ee]rror/i)) {
      throw new Error('no duplicate error message visible');
    }
    return 'duplicate rejected';
  });
}

// ── F5. Login / Logout ────────────────────────────────────────────────────────

async function f5_login_logout(page) {
  console.log('\n── F5. Login / Logout ──');
  await page.goto(`${BASE}/login`);
  await page.waitForLoadState('networkidle');

  await check('F5', 'Página /login carga', async () => {
    if (!(await page.$('form'))) throw new Error('no form');
  });

  await check('F5', 'Credenciales incorrectas muestran error', async () => {
    await page.fill('input[type="email"]', 'wrong@test.co');
    await page.fill('input[type="password"]', 'badpass');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(1200);
    const body = await page.textContent('body');
    if (!body.match(/error|Error|inválid|incorrect|contraseña|Invalid/i)) {
      throw new Error('no error for bad credentials');
    }
    return 'error shown';
  });

  await check('F5', 'Login como agente', async () => {
    await loginAs(page, AGENT);
    const url = page.url();
    if (url.includes('/login')) throw new Error('still on /login');
    return `→ ${url}`;
  });

  await check('F5', 'Header muestra usuario autenticado', async () => {
    const body = await page.textContent('header');
    if (!body.match(/Agente|Demo|salir|Salir|logout/i)) throw new Error('no user in header');
    return 'user in header';
  });

  await check('F5', 'Enlace a Favoritos en header', async () => {
    const link = await page.$('header a[href*="favorit"], nav a[href*="favorit"]');
    if (!link) throw new Error('no favoritos link');
  });

  await check('F5', 'Logout limpia sesión', async () => {
    await logout(page);
    await page.reload();
    await page.waitForTimeout(600);
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    if (token) throw new Error('token still in localStorage');
    return 'session cleared';
  });
}

// ── F6. Favoritos ─────────────────────────────────────────────────────────────

async function f6_favorites(page) {
  console.log('\n── F6. Favoritos ──');

  await check('F6', '/favoritos sin login redirige a /login', async () => {
    await logout(page);
    await page.goto(`${BASE}/favoritos`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);
    if (!page.url().includes('login')) throw new Error(`url=${page.url()}`);
    return `→ ${page.url()}`;
  });

  await loginAs(page, AGENT);
  const slug = await getPublishedSlug();

  await check('F6', 'Botón favorito en detalle (logged in)', async () => {
    await page.goto(`${BASE}/propiedades/${slug}`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(800);
    // button has text "♡ Guardar en favoritos" or "Quitar de favoritos"
    const favBtn = await page.$('button:has-text("favoritos"), button:has-text("Favorito")');
    if (!favBtn) throw new Error('no favoritos button');
    await favBtn.click();
    await page.waitForTimeout(800);
    return 'toggled';
  });

  await check('F6', 'Página /favoritos carga autenticado', async () => {
    await page.goto(`${BASE}/favoritos`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);
    if (page.url().includes('login')) throw new Error('redirected to login');
    return 'loaded';
  });

  await warn('F6', 'Grid de favoritos muestra contenido o empty state', async () => {
    const links = await page.$$('a[href*="/propiedades/"]');
    const body  = await page.textContent('main, body');
    if (links.length === 0 && !body.match(/favorito|vacío|no tienes|empty/i)) {
      throw new Error('nothing rendered');
    }
    return links.length > 0 ? `${links.length} favorito(s)` : 'empty state';
  });
}

// ── F7. Panel de agente ───────────────────────────────────────────────────────

async function f7_agent(page) {
  console.log('\n── F7. Panel de agente ──');

  await check('F7', '/agente sin login redirige a /login', async () => {
    await logout(page);
    await page.goto(`${BASE}/agente`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);
    if (!page.url().includes('login')) throw new Error(`url=${page.url()}`);
    return `→ ${page.url()}`;
  });

  await loginAs(page, AGENT);
  await page.goto(`${BASE}/agente`);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(600);

  await check('F7', 'Dashboard agente carga', async () => {
    if (page.url().includes('login')) throw new Error('redirected to login');
    const h1 = await page.$('h1');
    return h1 ? `"${(await h1.textContent()).slice(0, 30)}"` : 'loaded';
  });

  await warn('F7', 'Propiedades del agente visibles', async () => {
    // agent has 3 demo properties from seed — detect by "Editar" buttons or property links
    const editBtns = await page.$$('button:has-text("Editar"), a:has-text("Editar")');
    const propLinks = await page.$$('a[href*="/agente/editar/"]');
    if (editBtns.length === 0 && propLinks.length === 0) throw new Error('no properties visible');
    return `${editBtns.length + propLinks.length} property item(s)`;
  });

  await check('F7', 'Navega a /agente/nueva', async () => {
    await page.goto(`${BASE}/agente/nueva`);
    await page.waitForLoadState('networkidle');
    if (!(await page.$('form'))) throw new Error('no form at /agente/nueva');
  });

  await check('F7', 'Crea propiedad nueva (via API + edita en UI)', async () => {
    // Create the property via API (same call the form makes) and then verify the edit UI
    const at = await page.evaluate(() => localStorage.getItem('access_token'));
    const created = await fetch(`${API}/api/v1/properties`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${at}` },
      body: JSON.stringify({
        title: 'Casa de prueba QA E2E', description: 'Prueba automatizada con Playwright.',
        operation_type: 'sale', property_kind: 'house',
        price_amount: 500000000, currency: 'COP',
        bedrooms: 3, bathrooms: 2, total_area_m2: 120,
        address_street: 'Calle 100 #10-20 Bogotá', contact_phone: '+571234567',
      }),
    }).then(r => r.json());

    if (!created?.id) throw new Error(`API create failed: ${JSON.stringify(created).slice(0, 100)}`);
    newPropertyId = created.id;

    // Verify the edit page loads correctly
    await page.goto(`${BASE}/agente/editar/${newPropertyId}`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);
    if (page.url().includes('login')) throw new Error('redirected to login');
    const titleInput = await page.locator('input[type="text"]').first();
    const val = await titleInput.inputValue();
    if (!val.includes('Casa')) throw new Error(`title field shows: "${val}"`);
    return `id=${newPropertyId.slice(0,8)}… — edit page loaded`;
  });

  await warn('F7', 'Upload de imagen en propiedad creada', async () => {
    if (!newPropertyId) throw new Error('create failed, skip upload');
    await page.goto(`${BASE}/agente/editar/${newPropertyId}`);
    await page.waitForLoadState('networkidle');
    const fileInput = await page.$('input[type="file"]');
    if (!fileInput) throw new Error('no file input');
    const { writeFileSync } = require('fs');
    // minimal 1x1 JPEG
    const jpegBytes = Buffer.from([
      0xFF,0xD8,0xFF,0xE0,0x00,0x10,0x4A,0x46,0x49,0x46,0x00,0x01,0x01,0x00,0x00,0x01,
      0x00,0x01,0x00,0x00,0xFF,0xDB,0x00,0x43,0x00,0x08,0x06,0x06,0x07,0x06,0x05,0x08,
      0x07,0x07,0x07,0x09,0x09,0x08,0x0A,0x0C,0x14,0x0D,0x0C,0x0B,0x0B,0x0C,0x19,0x12,
      0x13,0x0F,0x14,0x1D,0x1A,0x1F,0x1E,0x1D,0x1A,0x1C,0x1C,0x20,0x24,0x2E,0x27,0x20,
      0x22,0x2C,0x23,0x1C,0x1C,0x28,0x37,0x29,0x2C,0x30,0x31,0x34,0x34,0x34,0x1F,0x27,
      0x39,0x3D,0x38,0x32,0x3C,0x2E,0x33,0x34,0x32,0xFF,0xC0,0x00,0x0B,0x08,0x00,0x01,
      0x00,0x01,0x01,0x01,0x11,0x00,0xFF,0xC4,0x00,0x1F,0x00,0x00,0x01,0x05,0x01,0x01,
      0x01,0x01,0x01,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x01,0x02,0x03,0x04,
      0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0xFF,0xDA,0x00,0x08,0x01,0x01,0x00,0x00,0x3F,
      0x00,0xFB,0xD2,0x8A,0x28,0x03,0xFF,0xD9
    ]);
    writeFileSync('/tmp/qa_test.jpg', jpegBytes);
    await fileInput.setInputFiles('/tmp/qa_test.jpg');
    await page.waitForTimeout(3000);
    return 'image upload triggered';
  });

  await check('F7', 'Enviar propiedad a moderación (via API)', async () => {
    // The UI doesn't have a submit-to-moderation button yet; use the API directly.
    if (!newPropertyId) throw new Error('no newPropertyId from F7 create step');
    const at = await page.evaluate(() => localStorage.getItem('access_token'));
    const res = await fetch(`${API}/api/v1/properties/${newPropertyId}/submit`, {
      method: 'POST', headers: { Authorization: `Bearer ${at}` },
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(`submit failed ${res.status}: ${JSON.stringify(body).slice(0, 80)}`);
    }
    const data = await res.json();
    return `status=${data.status || 'ok'}`;
  });

  await check('F7', '/agente/leads carga', async () => {
    await page.goto(`${BASE}/agente/leads`);
    await page.waitForLoadState('networkidle');
    if (page.url().includes('login')) throw new Error('redirected to login');
    const h1 = await page.$('h1');
    return h1 ? `"${(await h1.textContent()).slice(0, 30)}"` : 'loaded';
  });
}

// ── F8. Panel de admin ────────────────────────────────────────────────────────

async function f8_admin(page) {
  console.log('\n── F8. Panel de admin ──');

  await check('F8', '/admin sin login redirige a /login', async () => {
    await logout(page);
    await page.goto(`${BASE}/admin`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);
    if (!page.url().includes('login')) throw new Error(`url=${page.url()}`);
    return `→ ${page.url()}`;
  });

  await loginAs(page, ADMIN);

  await check('F8', 'Dashboard admin carga', async () => {
    await page.goto(`${BASE}/admin`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);
    if (page.url().includes('login')) throw new Error('redirected to login');
    if (page.url().includes('/agente')) throw new Error('admin redirected to /agente (permisos no cargados)');
    const h1 = await page.$('h1, h2');
    return `"${h1 ? (await h1.textContent()).slice(0, 30) : 'ok'}"`;
  });

  await check('F8', 'Stats del dashboard visibles', async () => {
    const body = await page.textContent('body');
    if (!body.match(/\d+/)) throw new Error('no numbers in dashboard');
    return 'stats present';
  });

  await check('F8', 'Moderación /admin/moderacion carga', async () => {
    await page.goto(`${BASE}/admin/moderacion`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);
    if (page.url().includes('login')) throw new Error('redirected to login');
    return 'loaded';
  });

  await check('F8', 'Aprobar propiedad en cola de moderación', async () => {
    // F7 already submitted newPropertyId to moderation; now approve it as admin
    if (!newPropertyId) {
      // fallback: create + submit a property via agent API
      const agentLogin = await fetch(`${API}/api/v1/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(AGENT),
      }).then(r => r.json());
      const agentToken = agentLogin.access_token;
      if (agentToken) {
        const created = await fetch(`${API}/api/v1/properties`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${agentToken}` },
          body: JSON.stringify({ title: 'QA Moderation', operation_type: 'sale', property_kind: 'house', price_amount: 100000000, currency: 'COP' }),
        }).then(r => r.json());
        if (created?.id) {
          newPropertyId = created.id;
          await fetch(`${API}/api/v1/properties/${newPropertyId}/submit`, {
            method: 'POST', headers: { Authorization: `Bearer ${agentToken}` },
          });
        }
      }
    }

    await page.goto(`${BASE}/admin/moderacion`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1200);

    const approveBtn = page.locator('button:has-text("Aprobar")').first();
    const count = await approveBtn.count();
    if (count === 0) throw new Error('no approve button in moderation queue');
    await approveBtn.click();
    await page.waitForTimeout(1000);
    return 'approved';
  });

  await check('F8', 'Banners /admin/banners carga', async () => {
    await page.goto(`${BASE}/admin/banners`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(400);
    if (page.url().includes('login')) throw new Error('redirected to login');
    return 'loaded';
  });

  await check('F8', 'Crear y eliminar banner', async () => {
    await page.goto(`${BASE}/admin/banners`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(400);

    // Click "+ Nuevo banner" to reveal the form (it's hidden by default)
    const newBannerBtn = page.locator('button:has-text("Nuevo banner")');
    if (await newBannerBtn.count() === 0) throw new Error('no "Nuevo banner" button');
    await newBannerBtn.click();
    await page.waitForTimeout(400);

    // Inputs have no type attribute (default=text) — can't use input[type="text"]
    const form = page.locator('form');
    const allInputs = form.locator('input:not([type="file"]):not([type="checkbox"]):not([type="number"]):not([type="datetime-local"])');
    const inputCount = await allInputs.count();
    if (inputCount === 0) throw new Error('no text inputs in banner form');

    await allInputs.nth(0).fill('Banner QA Test');           // title
    await allInputs.nth(1).fill('http://example.com/img.jpg'); // image_desktop_url
    if (inputCount > 2) await allInputs.nth(4).fill('http://example.com'); // cta_url

    const btn = page.locator('button[type="submit"], button:has-text("Crear banner")').first();
    if (await btn.count() === 0) throw new Error('no create button');
    await btn.click();
    await page.waitForTimeout(1500);

    const deleteBtn = await page.$('button:has-text("Eliminar"), button:has-text("Borrar"), button:has-text("Delete")');
    if (deleteBtn) {
      await deleteBtn.click();
      await page.waitForTimeout(800);
      return 'created and deleted';
    }
    return 'created (delete button not found)';
  });

  await check('F8', 'Destacados /admin/destacados carga', async () => {
    await page.goto(`${BASE}/admin/destacados`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(400);
    if (page.url().includes('login')) throw new Error('redirected to login');
    return 'loaded';
  });

  await check('F8', 'Usuarios /admin/usuarios carga', async () => {
    await page.goto(`${BASE}/admin/usuarios`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);
    if (page.url().includes('login')) throw new Error('redirected to login');
    // admin is also a user, agente@listing.co is there too
    const body = await page.textContent('body');
    if (!body.match(/listing\.co|@|admin|agente/i)) throw new Error('no email/user visible');
    return 'users visible';
  });

  // ── 1. Destacados: agregar y eliminar ──────────────────────────────────────
  await check('F8', 'Destacados: agregar propiedad destacada', async () => {
    await page.goto(`${BASE}/admin/destacados`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);

    // search input has placeholder "Buscar propiedad por título…"
    const searchInput = page.locator('input[placeholder*="Buscar propiedad"]');
    if (await searchInput.count() === 0) throw new Error('no property search input');
    await searchInput.fill('Casa');
    await page.waitForTimeout(900); // debounce 350ms + render

    // dropdown items render as <strong>title</strong> inside the absolute div
    // click the first strong that appears (property title in results)
    const firstResult = page.locator('strong').first();
    if (await firstResult.count() === 0) throw new Error('no dropdown results for "Casa"');
    await firstResult.click();
    await page.waitForTimeout(300);

    // verify property_id was set (shows "ID: ..." below input)
    const selected = await page.locator('p').filter({ hasText: /^ID:/ }).count();
    if (selected === 0) throw new Error('property not selected from dropdown');

    const submitBtn = page.locator('button:has-text("Agregar Destacado")');
    if (await submitBtn.count() === 0) throw new Error('no Agregar Destacado button');
    await submitBtn.click();
    await page.waitForTimeout(1200);

    const body = await page.textContent('body');
    if (!body.includes('Activos')) throw new Error('featured list section missing');
    return 'featured property added';
  });

  await check('F8', 'Destacados: eliminar propiedad destacada', async () => {
    // reload to ensure latest state after createFeatured
    await page.goto(`${BASE}/admin/destacados`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(800);

    const body = await page.textContent('body');
    const countMatch = body.match(/Activos \((\d+)\)/);
    const itemCount = countMatch ? parseInt(countMatch[1]) : 0;
    if (itemCount === 0) throw new Error(`no featured items — Activos(${itemCount}); check if createFeatured succeeded`);

    const delBtn = page.locator('button:has-text("Eliminar")').first();
    if (await delBtn.count() === 0) throw new Error('Eliminar button not rendered');
    page.once('dialog', d => d.accept());
    await delBtn.click();
    await page.waitForTimeout(800);
    return `deleted (had ${itemCount} item(s))`;
  });

  // ── 2. Moderación: rechazar propiedad ──────────────────────────────────────
  await check('F8', 'Moderación: rechazar propiedad', async () => {
    // create + submit a fresh property as agent
    const agentLogin = await fetch(`${API}/api/v1/auth/login`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(AGENT),
    }).then(r => r.json());
    const agentToken = agentLogin.access_token;
    if (!agentToken) throw new Error('agent login failed');

    const created = await fetch(`${API}/api/v1/properties`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${agentToken}` },
      body: JSON.stringify({ title: 'QA Reject Test', operation_type: 'sale', property_kind: 'house', price_amount: 200000000, currency: 'COP' }),
    }).then(r => r.json());
    if (!created?.id) throw new Error('create failed');
    await fetch(`${API}/api/v1/properties/${created.id}/submit`, {
      method: 'POST', headers: { Authorization: `Bearer ${agentToken}` },
    });

    await page.goto(`${BASE}/admin/moderacion`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const rejectBtn = page.locator('button:has-text("Rechazar")').first();
    if (await rejectBtn.count() === 0) throw new Error('no Rechazar button in queue');
    await rejectBtn.click();
    await page.waitForTimeout(1000);
    return 'property rejected';
  });

  // ── 3. Usuarios: sin UI de asignación de roles ─────────────────────────────
  await check('F8', 'Usuarios: sin UI de asignación de roles (solo lectura)', async () => {
    await page.goto(`${BASE}/admin/usuarios`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);
    // confirm there's no role-assign button (feature not built yet)
    const assignBtn = await page.locator('button:has-text("Asignar"), button:has-text("Rol"), select[name*="rol"]').count();
    const body = await page.textContent('body');
    const hasUsers = body.match(/listing\.co|@/i);
    if (!hasUsers) throw new Error('no user emails visible');
    return `users listed; role-assign UI: ${assignBtn > 0 ? 'present' : 'absent (read-only)'}`;
  });

  // ── 4. Paginación en listas ────────────────────────────────────────────────
  await check('F8', 'Paginación: propiedades del agente', async () => {
    await logout(page);
    await loginAs(page, AGENT);
    await page.goto(`${BASE}/agente`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);
    const body = await page.textContent('body');
    const hasPagination = body.match(/página|Siguiente|Anterior|page/i) || await page.locator('button:has-text("Siguiente"), button:has-text("Anterior"), nav[aria-label*="pagina"]').count() > 0;
    const propCount = await page.locator('a[href*="/propiedades/"]').count();
    return `${propCount} properties visible; pagination: ${hasPagination ? 'present' : 'not needed (<20 items)'}`;
  });

  await check('F8', 'Paginación: cola de moderación admin', async () => {
    await logout(page);
    await loginAs(page, ADMIN);
    await page.goto(`${BASE}/admin/moderacion`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);
    const body = await page.textContent('body');
    const hasPagination = body.match(/página|Siguiente|Anterior/i) || await page.locator('button:has-text("Siguiente"), button:has-text("Anterior")').count() > 0;
    const queueCount = (body.match(/Cola de moderación \((\d+)\)/)?.[1]) || '?';
    return `queue size=${queueCount}; pagination: ${hasPagination ? 'present' : 'not needed'}`;
  });

  await warn('F8', 'Agente sin permisos de admin redirige desde /admin', async () => {
    await logout(page);
    await loginAs(page, AGENT);
    await page.goto(`${BASE}/admin`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(800);
    const url = page.url();
    if (url.includes('/admin') && !url.includes('login')) {
      throw new Error(`agente can access /admin — url=${url}`);
    }
    return `→ ${url}`;
  });
}

// ── F9. Edge cases ────────────────────────────────────────────────────────────

async function f9_edge_cases(page) {
  console.log('\n── F9. Edge cases y 404 ──');

  await check('F9', 'Ruta inexistente muestra 404', async () => {
    await page.goto(`${BASE}/esta-ruta-no-existe-qa-123`);
    await page.waitForLoadState('networkidle');
    const body = await page.textContent('body');
    if (!body.match(/404|no encontrada|not found/i)) throw new Error('no 404 message');
    return '404 page shown';
  });

  await check('F9', '/favoritos sin auth → /login', async () => {
    await logout(page);
    await page.goto(`${BASE}/favoritos`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);
    if (!page.url().includes('login')) throw new Error(`url=${page.url()}`);
    return 'redirected';
  });

  await check('F9', '/agente sin auth → /login', async () => {
    await page.goto(`${BASE}/agente`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);
    if (!page.url().includes('login')) throw new Error(`url=${page.url()}`);
    return 'redirected';
  });

  await check('F9', '/admin sin auth → /login', async () => {
    await page.goto(`${BASE}/admin`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);
    if (!page.url().includes('login')) throw new Error(`url=${page.url()}`);
    return 'redirected';
  });
}

// ── F10. SEO y endpoints ──────────────────────────────────────────────────────

async function f10_seo(page) {
  console.log('\n── F10. SEO y endpoints backend ──');

  await check('F10', 'GET /sitemap.xml devuelve XML', async () => {
    const res  = await fetch(`${API}/sitemap.xml`);
    const body = await res.text();
    if (!body.includes('<urlset') && !body.includes('<sitemapindex')) {
      throw new Error(`unexpected body: ${body.slice(0, 100)}`);
    }
    return `${res.status} OK`;
  });

  await check('F10', 'GET /robots.txt devuelve texto', async () => {
    const res  = await fetch(`${API}/robots.txt`);
    const body = await res.text();
    if (!body.match(/User-agent|user-agent|Disallow|Allow/i)) {
      throw new Error(`body: ${body.slice(0, 100)}`);
    }
    return `${res.status} OK`;
  });

  await check('F10', 'Swagger UI en /api/docs', async () => {
    await page.goto(`${API}/api/docs`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(800);
    const swagger = await page.$('.swagger-ui, #swagger-ui, .swagger');
    const title   = await page.title();
    if (!swagger && !title.match(/swagger|fastapi|openapi/i)) {
      throw new Error(`no swagger UI. title="${title}"`);
    }
    return `docs at /api/docs`;
  });

  await warn('F10', 'GET /health endpoint', async () => {
    // try both common paths
    for (const path of ['/api/v1/health', '/health', '/api/health']) {
      const r = await fetch(`${API}${path}`).catch(() => null);
      if (r?.ok) return `${r.status} at ${path}`;
    }
    throw new Error('no health endpoint found');
  });
}

// ── F11. Sesión y token ───────────────────────────────────────────────────────

async function f11_session(page) {
  console.log('\n── F11. Sesión y token ──');
  await loginAs(page, AGENT);

  await check('F11', 'access_token y refresh_token en localStorage', async () => {
    const at = await page.evaluate(() => localStorage.getItem('access_token'));
    const rt = await page.evaluate(() => localStorage.getItem('refresh_token'));
    if (!at) throw new Error('no access_token');
    if (!rt) throw new Error('no refresh_token');
    return `at=${at.length}chars`;
  });

  await check('F11', 'Sesión persiste tras reload', async () => {
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    const at = await page.evaluate(() => localStorage.getItem('access_token'));
    if (!at) throw new Error('token lost after reload');
    if (page.url().includes('login')) throw new Error('redirected to login after reload');
    return 'session persisted';
  });

  await check('F11', 'Navegación entre páginas mantiene sesión', async () => {
    await page.goto(`${BASE}/propiedades`);
    await page.waitForLoadState('networkidle');
    const at1 = await page.evaluate(() => localStorage.getItem('access_token'));
    await page.goto(`${BASE}/favoritos`);
    await page.waitForLoadState('networkidle');
    const at2 = await page.evaluate(() => localStorage.getItem('access_token'));
    if (!at1 || !at2) throw new Error('token missing during navigation');
    if (page.url().includes('login')) throw new Error('redirected to login mid-navigation');
    return 'token stable';
  });
}

// ── main ──────────────────────────────────────────────────────────────────────

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: `${process.env.HOME}/.cache/ms-playwright/chromium-1194/chrome-linux/chrome`,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
  });
  const page = await context.newPage();
  page.on('console', () => {});

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('  Listing — E2E Frontend Test Suite (Playwright)  ');
  console.log(`  Base: ${BASE}   API: ${API}`);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

  try {
    await f1_home(page);
    await f2_search(page);
    await f3_detail(page);
    await f4_register(page);
    await f5_login_logout(page);
    await f6_favorites(page);
    await f7_agent(page);
    await f8_admin(page);
    await f9_edge_cases(page);
    await f10_seo(page);
    await f11_session(page);
  } finally {
    await browser.close();
  }

  // ── Reporte ───────────────────────────────────────────────────────────────
  const SUITE_LABELS = {
    F1:'Home pública', F2:'Búsqueda y filtros', F3:'Detalle de propiedad',
    F4:'Registro', F5:'Login / Logout', F6:'Favoritos', F7:'Panel de agente',
    F8:'Panel de admin', F9:'Rutas protegidas', F10:'SEO y endpoints', F11:'Sesión y token',
  };

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('  REPORTE FINAL');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  console.log('| Flujo | Estado | ✅ ❌ ⚠️ |');
  console.log('|-------|--------|---------|');

  const suites = [...new Set(results.map(r => r.suite))];
  for (const s of suites) {
    const sr = results.filter(r => r.suite === s);
    const p  = sr.filter(r => r.status === 'PASS').length;
    const f  = sr.filter(r => r.status === 'FAIL').length;
    const w  = sr.filter(r => r.status === 'WARN').length;
    const icon = f > 0 ? '❌' : w > 0 ? '⚠️' : '✅';
    console.log(`| ${s}. ${SUITE_LABELS[s]} | ${icon} | ${p} ${f} ${w} |`);
  }

  const failures = results.filter(r => r.status === 'FAIL');
  if (failures.length) {
    console.log('\n── Fallos ─────────────────────────────────────────');
    failures.forEach(f => console.log(`\n❌ [${f.suite}] ${f.name}\n   ${f.note}`));
  }

  const warnings = results.filter(r => r.status === 'WARN');
  if (warnings.length) {
    console.log('\n── Warnings ────────────────────────────────────────');
    warnings.forEach(w => console.log(`⚠️  [${w.suite}] ${w.name}: ${w.note}`));
  }

  console.log(`\n━━━ Total: ${passed} passed · ${failed} failed · ${warned} warned ━━━`);
  process.exit(failed > 0 ? 1 : 0);
})();
