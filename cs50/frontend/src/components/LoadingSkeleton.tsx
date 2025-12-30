import './LoadingSkeleton.css';

interface LoadingSkeletonProps {
  width?: string;
  height?: string;
  borderRadius?: string;
  className?: string;
}

export default function LoadingSkeleton({
  width = '100%',
  height = '1rem',
  borderRadius = '4px',
  className = '',
}: LoadingSkeletonProps) {
  return (
    <div
      className={`skeleton ${className}`}
      style={{ width, height, borderRadius }}
      aria-hidden="true"
    />
  );
}

export function DeckCardSkeleton() {
  return (
    <div className="deck-card-skeleton">
      <LoadingSkeleton height="1.5rem" width="60%" className="skeleton-title" />
      <LoadingSkeleton height="1rem" width="100%" className="skeleton-description" />
      <LoadingSkeleton height="1rem" width="40%" className="skeleton-footer" />
    </div>
  );
}

export function CardItemSkeleton() {
  return (
    <div className="card-item-skeleton">
      <LoadingSkeleton height="1.25rem" width="80%" className="skeleton-question" />
      <LoadingSkeleton height="1rem" width="100%" className="skeleton-explanation" />
      <LoadingSkeleton height="0.875rem" width="60%" className="skeleton-stats" />
    </div>
  );
}
