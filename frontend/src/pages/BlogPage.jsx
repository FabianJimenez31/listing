import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { getPosts } from '../api/blog'
import Spinner from '../components/ui/Spinner'

export default function BlogPage() {
  const [posts, setPosts] = useState(null)

  useEffect(() => {
    getPosts({ page_size: 12 }).then((r) => setPosts(r?.data || [])).catch(() => setPosts([]))
  }, [])

  return (
    <div className="page-wrap">
      <Helmet>
        <title>Blog de inversión | Proppietario</title>
        <meta name="description" content="Guías y análisis de inversión inmobiliaria en Colombia y Estados Unidos." />
      </Helmet>

      <div className="sec-head" style={{ marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 28 }}>Blog de inversión</h2>
          <p>Guías, análisis y oportunidades del mercado inmobiliario</p>
        </div>
      </div>

      {posts === null ? (
        <Spinner />
      ) : posts.length === 0 ? (
        <p style={{ color: 'var(--muted)' }}>Pronto publicaremos contenido.</p>
      ) : (
        <div className="grid-blog">
          {posts.map((p) => (
            <Link key={p.id} className="post-card" to={`/blog/${p.slug}`}>
              <div className="ph">
                {p.cover_image_url && (
                  <img
                    src={p.cover_image_url}
                    alt={p.title}
                    onError={(e) => { e.currentTarget.src = `https://picsum.photos/seed/${p.slug}/600/360` }}
                  />
                )}
              </div>
              <div className="pb">
                {p.category && <div className="cat">{p.category}</div>}
                <h3>{p.title}</h3>
                {p.excerpt && <p>{p.excerpt}</p>}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
