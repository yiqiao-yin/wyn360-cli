import React from 'react';
// import AISearch from '../components/AISearch';

// Root component that wraps the entire Docusaurus app
// Custom AISearch disabled in favor of native Docusaurus local search
export default function Root({children}: {children: React.ReactNode}): JSX.Element {
  return (
    <>
      {children}
      {/* Custom AISearch component disabled - using native Docusaurus search instead */}
      {/*
      <div style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        zIndex: 1000,
        maxWidth: '400px'
      }}>
        <AISearch />
      </div>
      */}
    </>
  );
}