import assert from 'node:assert/strict'
import test from 'node:test'

import { prioritizeMainImage } from './imageOrder.js'

test('the selected cover is shown first without changing the remaining order', () => {
  const images = [
    { id: 'one', role: 'gallery' },
    { id: 'two', role: 'gallery' },
    { id: 'cover', role: 'main' },
    { id: 'three', role: 'gallery' },
  ]

  assert.deepEqual(
    prioritizeMainImage(images).map((image) => image.id),
    ['cover', 'one', 'two', 'three'],
  )
})

test('an image list without a cover keeps its original order', () => {
  const images = [{ id: 'one', role: 'gallery' }, { id: 'two', role: 'gallery' }]

  assert.equal(prioritizeMainImage(images), images)
})
