import React from 'react';
import AISearch from '../components/AISearch';

// Root component that wraps the entire Docusaurus app
export default function Root({children}: {children: React.ReactNode}): JSX.Element {
  return (
    <>
      {children}
      <div style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        zIndex: 1000,
        maxWidth: '400px'
      }}>
        <AISearch />
      </div>
    </>
  );
}