/* Consistent page header for every admin screen: title, optional count,
   subtitle and an actions slot (buttons rendered on the right). */
export default function AdminPageHeader({ title, subtitle, count, actions }) {
  return (
    <header className="admin-pagehead">
      <div className="admin-pagehead-text">
        <h1>
          {title}
          {typeof count === 'number' && <span className="admin-count">{count}</span>}
        </h1>
        {subtitle && <p className="sub">{subtitle}</p>}
      </div>
      {actions && <div className="admin-pagehead-actions">{actions}</div>}
    </header>
  )
}
