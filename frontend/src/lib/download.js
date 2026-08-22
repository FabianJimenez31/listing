/**
 * Browser file downloads for authenticated API responses.
 *
 * A plain <a href> cannot download from the API: the endpoints need the Bearer
 * token, so the file arrives as an axios blob and is handed to the browser here.
 */

// Filename the server proposed in Content-Disposition, else the fallback.
export const filenameFrom = (response, fallback) => {
  const header = response?.headers?.['content-disposition'] || ''
  const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(header)
  return match ? decodeURIComponent(match[1]) : fallback
}

// Hand a blob to the browser as a download, then release the object URL.
export const saveBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

// Convenience: save an axios blob response with its server-given name.
export const saveResponse = (response, fallbackName) =>
  saveBlob(response.data, filenameFrom(response, fallbackName))
