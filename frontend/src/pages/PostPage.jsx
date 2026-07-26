import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { getPost } from '../api/blog'
import Spinner from '../components/ui/Spinner'

export default function PostPage() {
  const { slug } = useParams()
  const [post, setPost] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    setLoading(true)
    setError(false)
    getPost(slug).then(setPost).catch(() => setError(true)).finally(() => setLoading(false))
  }, [slug])

  if (loading) return <div className="page-wrap"><Spinner /></div>
  if (error || !post) {
    return (
      <div className="page-wrap">
        <p>Artículo no encontrado.</p>
        <Link to="/blog" className="seelink">← Volver al blog</Link>
      </div>
    )
  }

  return (
    <article className="page-wrap" style={{ maxWidth: 820 }}>
      <Helmet><title>{`${post.title} | Proppia`}</title></Helmet>
      <div className="crumbs"><Link to="/blog">Blog</Link>{post.category ? ` · ${post.category}` : ''}</div>
      <h1 style={{ fontSize: 'clamp(26px,4vw,40px)', fontWeight: 800, color: 'var(--ink)', margin: '8px 0 18px', lineHeight: 1.15 }}>
        {post.title}
      </h1>
      {post.cover_image_url && (
        <img
          src={post.cover_image_url}
          alt={post.title}
          style={{ width: '100%', height: 380, objectFit: 'cover', borderRadius: 'var(--radius-lg)', marginBottom: 24 }}
          onError={(e) => { e.currentTarget.src = `https://picsum.photos/seed/${post.slug}/1000/500` }}
        />
      )}
      {post.excerpt && <p style={{ fontSize: 18, color: 'var(--muted)', marginBottom: 18 }}>{post.excerpt}</p>}
      <div className="prose">
        {(post.content || '').split('\n').filter(Boolean).map((para, i) => <p key={i}>{para}</p>)}
      </div>
    </article>
  )
}
