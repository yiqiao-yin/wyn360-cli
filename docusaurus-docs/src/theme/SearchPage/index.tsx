import React from 'react';
import SearchPageOriginal from '@theme-original/SearchPage';
import AISearch from '../../components/AISearch';

export default function SearchPage(props: any): JSX.Element {
  return (
    <div>
      <AISearch />
      <SearchPageOriginal {...props} />
    </div>
  );
}