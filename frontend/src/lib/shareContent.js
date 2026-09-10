export async function shareContent({ title, url = window.location.href }) {
  if (navigator.share) {
    try {
      await navigator.share({ title, url })
      return 'shared'
    } catch (error) {
      if (error?.name === 'AbortError') return 'cancelled'
    }
  }
  await navigator.clipboard.writeText(url)
  return 'copied'
}
