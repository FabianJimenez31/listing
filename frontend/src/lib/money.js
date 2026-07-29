/**
 * Money helpers. The API stores prices in minor units (centavos = pesos × 100).
 * The UI always shows/accepts the MAJOR unit (pesos / dollars) — never centavos.
 */

// Keep only digits from arbitrary input.
export const digitsOnly = (s) => String(s ?? '').replace(/\D/g, '')

// "350000000" -> "350.000.000" (es-CO grouping). Empty input -> "".
export const groupThousands = (value) => {
  const d = digitsOnly(value)
  return d ? new Intl.NumberFormat('es-CO').format(Number(d)) : ''
}

// Major-unit digit string -> minor units for the API (or null when empty).
export const majorToMinor = (value) => {
  const d = digitsOnly(value)
  return d === '' ? null : parseInt(d, 10) * 100
}

// Minor units from the API -> major-unit digit string for the input.
export const minorToMajor = (minor) =>
  minor == null || minor === '' ? '' : String(Math.round(Number(minor) / 100))
