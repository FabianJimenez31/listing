import { useEffect, useMemo, useRef, useState } from 'react'
import { Viewer } from '@photo-sphere-viewer/core'
import { GalleryPlugin } from '@photo-sphere-viewer/gallery-plugin'
import { MarkersPlugin } from '@photo-sphere-viewer/markers-plugin'
import { VirtualTourPlugin } from '@photo-sphere-viewer/virtual-tour-plugin'
import '@photo-sphere-viewer/core/index.css'
import '@photo-sphere-viewer/gallery-plugin/index.css'
import '@photo-sphere-viewer/markers-plugin/index.css'
import '@photo-sphere-viewer/virtual-tour-plugin/index.css'
import TourAiNotice from './TourAiNotice'
import '../../styles/tour.css'

function panoData(scene) {
  if (!scene.width || !scene.height || (scene.hfov_deg === 360 && scene.vfov_deg === 180)) return undefined
  const fullWidth = Math.round(scene.width * (360 / scene.hfov_deg))
  const fullHeight = Math.round(scene.height * (180 / scene.vfov_deg))
  return {
    fullWidth,
    fullHeight,
    croppedWidth: scene.width,
    croppedHeight: scene.height,
    croppedX: Math.round((fullWidth - scene.width) / 2),
    croppedY: Math.round((fullHeight - scene.height) / 2),
  }
}

export default function TourViewer({ tour }) {
  const shellRef = useRef(null)
  const containerRef = useRef(null)
  const viewerRef = useRef(null)
  const pluginRef = useRef(null)
  const ordered = useMemo(() => [...tour.scenes].sort((a, b) => a.position - b.position), [tour])
  const initialId = tour.start_scene_id || ordered[0]?.id
  const [currentId, setCurrentId] = useState(initialId)
  const current = ordered.find((scene) => scene.id === currentId) || ordered[0]

  useEffect(() => {
    if (!containerRef.current || !ordered.length) return undefined
    const nodes = ordered.map((scene) => ({
      id: scene.id,
      panorama: scene.pano_url,
      thumbnail: scene.thumb_url || scene.pano_url,
      name: scene.title,
      caption: scene.title,
      panoData: panoData(scene),
      sphereCorrection: { pan: scene.initial_yaw || 0, tilt: scene.initial_pitch || 0 },
      links: scene.hotspots.map((spot) => ({
        nodeId: spot.to_scene_id,
        position: { yaw: spot.yaw, pitch: spot.pitch },
        data: { label: spot.label },
      })),
    }))
    const viewer = new Viewer({
      container: containerRef.current,
      navbar: ['zoom', 'move', 'autorotate'],
      plugins: [
        MarkersPlugin,
        GalleryPlugin.withConfig({ thumbnailSize: { width: 120, height: 70 } }),
        VirtualTourPlugin.withConfig({
          nodes,
          startNodeId: initialId,
          positionMode: 'manual',
          renderMode: '3d',
          showLinkTooltip: true,
        }),
      ],
    })
    const plugin = viewer.getPlugin(VirtualTourPlugin)
    const onChange = ({ node }) => setCurrentId(node.id)
    plugin.addEventListener('node-changed', onChange)
    viewerRef.current = viewer
    pluginRef.current = plugin
    return () => {
      plugin.removeEventListener('node-changed', onChange)
      viewer.destroy()
      viewerRef.current = null
      pluginRef.current = null
    }
  }, [ordered, initialId])

  const move = (direction) => {
    const index = ordered.findIndex((scene) => scene.id === currentId)
    const next = ordered[(index + direction + ordered.length) % ordered.length]
    if (next) pluginRef.current?.setCurrentNode(next.id)
  }

  const enterFullscreen = () => {
    const shell = shellRef.current
    if (shell?.requestFullscreen) shell.requestFullscreen()
    else if (shell?.webkitRequestFullscreen) shell.webkitRequestFullscreen()
  }

  return (
    <div ref={shellRef} className="tour-viewer-shell">
      <div ref={containerRef} className="tour-viewer" />
      {current?.source === 'ai' && <TourAiNotice />}
      <button type="button" className="tour-fullscreen" onClick={enterFullscreen}>⛶ Pantalla completa</button>
      {ordered.length > 1 && (
        <div className="tour-step-controls">
          <button type="button" onClick={() => move(-1)}>← Anterior</button>
          <strong>{current?.title}</strong>
          <button type="button" onClick={() => move(1)}>Siguiente →</button>
        </div>
      )}
    </div>
  )
}
