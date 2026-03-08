import * as React from 'react'

import { cn } from '../lib/utils'

export function ChartContainer({ className, children }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('rounded-[16px] border border-white/5 bg-black/20 p-2', className)}>
      {children}
    </div>
  )
}
