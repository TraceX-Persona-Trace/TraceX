interface Props {
  message: string
  onRetry?: () => void
}

export default function ErrorMessage({ message, onRetry }: Props) {
  return (
    <div style={styles.box}>
      <span style={styles.icon}>⚠</span>
      <span style={styles.text}>{message}</span>
      {onRetry && (
        <button style={styles.retry} onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  box: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.75rem 1rem',
    background: '#fff8f8',
    border: '1px solid #fca5a5',
    borderRadius: 6,
    color: '#b91c1c',
    fontSize: '0.875rem',
  },
  icon: { flexShrink: 0 },
  text: { flex: 1 },
  retry: {
    flexShrink: 0,
    padding: '0.2rem 0.6rem',
    border: '1px solid #fca5a5',
    borderRadius: 4,
    background: 'transparent',
    color: '#b91c1c',
    cursor: 'pointer',
    fontSize: '0.8rem',
  },
}
