import test from 'node:test'
import assert from 'node:assert/strict'

import { digitsOnly, groupThousands, normalizePriceRange } from './money.js'

test('formats pasted Colombian prices while retaining only digits', () => {
  assert.equal(digitsOnly('$ 350,000,000'), '350000000')
  assert.equal(groupThousands('350000000'), '350.000.000')
})

test('converts major units to minor units and repairs an inverted range', () => {
  assert.deepEqual(normalizePriceRange('600.000.000', '300.000.000'), {
    min_price: 30000000000,
    max_price: 60000000000,
  })
})
