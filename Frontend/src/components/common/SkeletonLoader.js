import React from 'react';

function SkeletonLoader({ type, count = 1 }) {
  const renderSkeletons = () => {
    const skeletons = [];
    for (let i = 0; i < count; i++) {
      skeletons.push(<div key={i} className={`skeleton-loader ${type}`}></div>);
    }
    return skeletons;
  };

  return <>{renderSkeletons()}</>;
}

export default SkeletonLoader;
