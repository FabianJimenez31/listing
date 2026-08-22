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

const DEG = Math.PI / 180
// Todas las flechas se proyectan a esta altura del piso, como Matterport.
const FLOOR_LINK_PITCH = -72 * DEG

export default function TourViewer({ tour }) {
  const shellRef = useRef(null)
  const containerRef = useRef(null)
  const viewerRef = useRef(null)
  const pluginRef = useRef(null)
  const ordered = useMemo(() => [...tour.scenes].sort((a, b) => a.position - b.position), [tour])
  // Grafo completo de hotspots por escena: la orientacion de llegada lo usa
  // aunque el visor solo muestre una flecha por escena (FR-407).
  const hotspotsByScene = useMemo(
    () => Object.fromEntries(ordered.map((scene) => [scene.id, scene.hotspots])),
    [ordered],
  )
  const initialId = tour.start_scene_id || ordered[0]?.id
  const [currentId, setCurrentId] = useState(initialId)
  const current = ordered.find((scene) => scene.id === currentId) || ordered[0]

  useEffect(() => {
    if (!ordered.length) return undefined
    // Precarga total del tour: todas las panoramicas se piden al montar para que
    // la navegacion posterior no descargue nada en vivo (FR-301/FR-302 del spec).
    const warm = ordered.map((scene) => {
      const img = new Image()
      img.decoding = 'async'
      img.src = scene.pano_url
      return img
    })
    return () => { warm.length = 0 }
  }, [ordered])

  useEffect(() => {
    if (!containerRef.current || !ordered.length) return undefined
    // Modo flecha unica (FR-407): cada escena muestra la flecha hacia la
    // escena siguiente del recorrido. Si el operador no creo ese enlace,
    // se sintetiza "continuar derecho": sale por el opuesto de la puerta de
    // llegada. Nunca queda una escena sin flecha.
    const straightYaw = (sceneId, fallback) => {
      const spots = hotspotsByScene[sceneId] || []
      if (!spots.length) return fallback
      const back = Math.atan2(Math.sin(spots[0].yaw), Math.cos(spots[0].yaw))
      return back + Math.PI
    }
    const nodes = ordered.map((scene, index) => {
      const prev = ordered[(index - 1 + ordered.length) % ordered.length]
      const next = ordered[(index + 1) % ordered.length]
      const nextSpot = scene.hotspots.find((spot) => spot.to_scene_id === next.id)
      const yaw = nextSpot
        ? nextSpot.yaw
        : straightYaw(scene.id, 0)
      return {
        id: scene.id,
        panorama: scene.pano_url,
        thumbnail: scene.thumb_url || scene.pano_url,
        name: scene.title,
        caption: scene.title,
        panoData: panoData(scene),
        sphereCorrection: { pan: scene.initial_yaw || 0, tilt: scene.initial_pitch || 0 },
        links: [{
          nodeId: next.id,
          position: {
            yaw: Math.atan2(Math.sin(yaw), Math.cos(yaw)),
            pitch: FLOOR_LINK_PITCH,
          },
          data: { label: nextSpot?.label || `Ir a ${next.title}` },
        }],
      }
    })
    const viewer = new Viewer({
      container: containerRef.current,
      navbar: ['zoom', 'move', 'fullscreen'],
      plugins: [
        MarkersPlugin,
        GalleryPlugin.withConfig({ thumbnailSize: { width: 120, height: 70 } }),
        VirtualTourPlugin.withConfig({
          nodes,
          startNodeId: initialId,
          positionMode: 'manual',
          renderMode: '3d',
          showLinkTooltip: true,
          preload: true,
          // Solo desvanecer flechas realmente superpuestas (45 por defecto
          // ocultaba salidas legitimas cercanas).
          arrowsPosition: { linkOverlapAngle: Math.PI / 8 },
          // Llegar mirando hacia adentro: opuesto al hotspot de retorno de la
          // escena destino (la entrada queda a la espalda), como Matterport.
          // PSV exige yaw y pitch completos en rotateTo. Se busca en el grafo
          // completo, no en las flechas visibles (solo hay una por escena).
          transitionOptions: (node, fromNode) => {
            if (!fromNode) return {}
            const backSpot = (hotspotsByScene[node.id] || []).find(
              (spot) => spot.to_scene_id === fromNode.id,
            )
            if (!backSpot) return {}
            return { rotateTo: { yaw: backSpot.yaw + Math.PI, pitch: 0 } }
          },
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
  }, [ordered, initialId, hotspotsByScene])

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
