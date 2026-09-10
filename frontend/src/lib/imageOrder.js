export function prioritizeMainImage(images = []) {
  const mainIndex = images.findIndex((image) => image.role === 'main')
  if (mainIndex <= 0) return images
  return [images[mainIndex], ...images.slice(0, mainIndex), ...images.slice(mainIndex + 1)]
}
