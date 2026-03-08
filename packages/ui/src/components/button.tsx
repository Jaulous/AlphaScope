import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '../lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-[16px] border border-[color:var(--border)] bg-[color:var(--card)] px-4 py-2 text-sm font-medium text-white transition-all hover:-translate-y-0.5 hover:border-white/15 hover:bg-white/5 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'shadow-[0_0_0_1px_rgb(255,255,255,0.08)]',
        ghost: 'border-transparent bg-transparent hover:bg-white/5',
        accent: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-300'
      },
      size: {
        default: 'h-10',
        sm: 'h-9 px-3',
        lg: 'h-11 px-5'
      }
    },
    defaultVariants: {
      variant: 'default',
      size: 'default'
    }
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }
