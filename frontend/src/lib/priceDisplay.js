export function formatPrice(amount, currency = 'COP') {
  if (amount == null) return null
  const locale = currency === 'USD' ? 'en-US' : 'es-CO'
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount / 100)
}
