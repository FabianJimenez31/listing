import { Fragment } from 'react'

/**
 * Renders a property description preserving the structure the agent wrote.
 *
 * Descriptions come from a free-text field and in practice carry real
 * structure: blank lines between groups, one emoji-bulleted item per line, and
 * `**markdown bold**` for sub-titles / labels. Rendered as a single <p> they
 * collapse into a wall of text with literal asterisks. Here we:
 *   - split into blocks on blank lines, and into lines within each block,
 *   - turn `**bold**` into real <strong> (no dangerouslySetInnerHTML — we build
 *     React nodes, so author text can never inject markup),
 *   - hang-indent emoji/dash bullet lines so wrapped text aligns,
 *   - give bold-only lines (e.g. "**Zonas comunes:**") a light heading look.
 */

const BOLD = /\*\*([^*]+)\*\*/g
// A line that starts with an emoji (or a dash/bullet glyph) reads as a list item.
const BULLET_START = /^(\p{Extended_Pictographic}|[-•·‣▪])/u
// Leading emoji + variation/zero-width selectors, used to peek past it.
const LEAD_EMOJI = /^\p{Extended_Pictographic}[️‍]*\s*/u

// Split a line into plain text + <strong> nodes around **bold** spans.
function renderInline(line, keyBase) {
  const nodes = []
  let last = 0
  let i = 0
  BOLD.lastIndex = 0
  let m
  while ((m = BOLD.exec(line)) !== null) {
    if (m.index > last) nodes.push(<Fragment key={`${keyBase}-t${i}`}>{line.slice(last, m.index)}</Fragment>)
    nodes.push(<strong key={`${keyBase}-b${i}`}>{m[1]}</strong>)
    last = m.index + m[0].length
    i += 1
  }
  if (last < line.length) nodes.push(<Fragment key={`${keyBase}-t${i}`}>{line.slice(last)}</Fragment>)
  return nodes
}

// A line that is essentially just a bold title (optionally emoji-prefixed).
function isHeading(line) {
  const rest = line.replace(LEAD_EMOJI, '').trim()
  return /^\*\*[^*]+\*\*:?$/.test(rest)
}

export default function PropertyDescription({ text }) {
  if (!text || !text.trim()) return null
  const clean = text.replace(/\r\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim()
  const blocks = clean.split(/\n{2,}/)

  return (
    <div className="pdp-desc">
      {blocks.map((block, bi) => {
        const lines = block.split('\n').map((l) => l.trim()).filter(Boolean)
        return (
          <div className="pdp-desc-block" key={bi}>
            {lines.map((line, li) => {
              const cls = isHeading(line) ? 'head' : (BULLET_START.test(line) ? 'bullet' : '')
              return (
                <p className={`pdp-desc-line${cls ? ` ${cls}` : ''}`} key={li}>
                  {renderInline(line, `${bi}-${li}`)}
                </p>
              )
            })}
          </div>
        )
      })}
    </div>
  )
}
