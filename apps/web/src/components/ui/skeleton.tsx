import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-lg bg-[#2A2A3E]", className)}
      {...props}
    />
  )
}

export { Skeleton }