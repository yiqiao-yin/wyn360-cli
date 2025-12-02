import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  // Custom sidebar matching MkDocs navigation structure
  tutorialSidebar: [
    'index',
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'getting-started/installation',
        'getting-started/quickstart',
        'getting-started/configuration',
      ],
    },
    {
      type: 'category',
      label: 'Features',
      items: [
        'features/overview',
        'features/web-search',
        'features/browser-use',
        'features/vision-mode',
        'features/github',
        'features/huggingface',
      ],
    },
    {
      type: 'category',
      label: 'Usage',
      items: [
        'usage/use-cases',
        'usage/commands',
        'usage/cost',
      ],
    },
    {
      type: 'category',
      label: 'Architecture',
      items: [
        'architecture/system',
        'architecture/autonomous-browsing',
      ],
    },
    {
      type: 'category',
      label: 'Development',
      items: [
        'development/contributing',
        'development/testing',
        'development/roadmap',
      ],
    },
  ],
};

export default sidebars;
