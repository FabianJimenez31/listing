// Canal de contacto para solicitudes de crédito hipotecario.
// Cambiar el número aquí lo actualiza en toda la sección (formulario y CTAs).
export const MORTGAGE_WHATSAPP_NUMBER = '573502752495'
export const MORTGAGE_WHATSAPP_DISPLAY = '+57 350 275 2495'

export const MORTGAGE_WHATSAPP_LINK = (text) =>
  `https://wa.me/${MORTGAGE_WHATSAPP_NUMBER}?text=${encodeURIComponent(text)}`
