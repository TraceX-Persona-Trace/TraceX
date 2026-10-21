export default function LoadingSpinner() {
  return (
    <div style={styles.wrapper}>
      <div style={styles.spinner} />
      <span style={styles.label}>Loading…</span>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '1rem 0',
    color: '#57606a',
    fontSize: '0.875rem',
  },
  spinner: {
    width: 18,
    height: 18,
    border: '2px solid #e5e7eb',
    borderTop: '2px solid #3b82d4',
    borderRadius: '50%',
    animation: 'tracex-spin 0.7s linear infinite',
  },
  label: {},
}

// Inject keyframes once
if (typeof document !== 'undefined' && !document.getElementById('tracex-spin-style')) {
  const s = document.createElement('style')
  s.id = 'tracex-spin-style'
  s.textContent = '@keyframes tracex-spin { to { transform: rotate(360deg); } }'
  document.head.appendChild(s)
}
