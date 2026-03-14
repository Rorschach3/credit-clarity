import { useEffect, useState } from "react"

interface AnimatedNumberProps extends React.HTMLAttributes<HTMLSpanElement> {
  value: number | string
  duration?: number // milliseconds
}

export function AnimatedNumber({ value, duration = 600, className, ...props }: AnimatedNumberProps) {
  const [display, setDisplay] = useState<string | number>(typeof value === 'number' ? 0 : value)

  useEffect(() => {
    if (typeof value !== 'number') {
      setDisplay(value)
      return
    }

    let start: number | null = null
    const startValue = typeof display === 'number' ? display : 0
    const diff = value - startValue

    function step(timestamp: number) {
      if (start === null) start = timestamp
      const progress = Math.min((timestamp - start) / duration, 1)
      setDisplay(Math.round(startValue + diff * progress))
      if (progress < 1) {
        requestAnimationFrame(step)
      }
    }

    requestAnimationFrame(step)
  }, [value, duration])

  return (
    <span className={className} {...props}>
      {display}
    </span>
  )
}
