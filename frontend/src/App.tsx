import { useState } from 'react'
import type { InvestigationResponse } from './api/types'
import InvestigationList from './components/InvestigationList'
import InvestigationDetail from './components/InvestigationDetail'

type View =
  | { name: 'list' }
  | { name: 'detail'; id: number }

export default function App() {
  const [view, setView] = useState<View>({ name: 'list' })

  function handleSelect(inv: InvestigationResponse) {
    setView({ name: 'detail', id: inv.id })
  }

  function handleBack() {
    setView({ name: 'list' })
  }

  if (view.name === 'detail') {
    return <InvestigationDetail id={view.id} onBack={handleBack} />
  }

  return <InvestigationList onSelect={handleSelect} />
}
