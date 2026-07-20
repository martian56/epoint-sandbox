import type { UseQueryResult } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useT } from '@/i18n'
import { EmptyState } from './Panel'

interface AsyncProps<T> {
  query: UseQueryResult<T>
  children: (data: T) => ReactNode
}

export function Async<T>({ query, children }: AsyncProps<T>) {
  const t = useT()

  if (query.isPending) {
    return <EmptyState title={t.common.loading} />
  }
  if (query.isError) {
    return <EmptyState title={t.common.apiUnreachable} hint={t.common.apiUnreachableHint} />
  }
  return <>{children(query.data)}</>
}
