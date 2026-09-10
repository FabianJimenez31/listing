import assert from 'node:assert/strict'
import test from 'node:test'

import { buildTourNodes } from './tourNodes.js'

const scene = (id, position) => ({
  id,
  position,
  title: `Scene ${id}`,
  pano_url: `/${id}.webp`,
  thumb_url: null,
  initial_yaw: 0,
  initial_pitch: 0,
  hfov_deg: 360,
  vfov_deg: 180,
  width: 2048,
  height: 1024,
  hotspots: [],
})

test('a single-scene tour never creates a link to itself', () => {
  const only = scene('only', 0)

  const nodes = buildTourNodes([only], { only: [] })

  assert.deepEqual(nodes[0].links, [])
})

test('a multi-scene tour keeps the ordered circular navigation', () => {
  const first = scene('first', 0)
  const second = scene('second', 1)

  const nodes = buildTourNodes([first, second], { first: [], second: [] })

  assert.equal(nodes[0].links[0].nodeId, 'second')
  assert.equal(nodes[1].links[0].nodeId, 'first')
})
