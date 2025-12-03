import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  Svg: React.ComponentType<React.ComponentProps<'svg'>>;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: '🤖 Multi-Provider AI Native',
    Svg: require('@site/static/img/undraw_docusaurus_mountain.svg').default,
    description: (
      <>
        Built on <strong>pydantic-ai</strong> framework with seamless integration across
        multiple AI providers: 🧠 <strong>Anthropic Claude</strong>, ☁️ <strong>AWS Bedrock</strong>,
        🌟 <strong>Google Gemini</strong>, and 🚀 <strong>OpenAI</strong>. Switch providers
        effortlessly based on your needs.
      </>
    ),
  },
  {
    title: '💰 Cost-Effective Intelligence',
    Svg: require('@site/static/img/undraw_docusaurus_tree.svg').default,
    description: (
      <>
        Save <strong>90% on costs</strong> compared to Microsoft Copilot! 🎯 Built-in
        <strong> slash commands</strong> let you customize token usage and track
        expenses in real-time. Get enterprise-grade AI assistance without the
        enterprise price tag. 📊
      </>
    ),
  },
  {
    title: '🔓 100% Open Source',
    Svg: require('@site/static/img/undraw_docusaurus_react.svg').default,
    description: (
      <>
        🐍 <strong>pip-installable</strong> and completely open source! Build upon our
        robust <strong>agentic framework</strong> for your custom use cases.
        Fork, extend, and contribute to the future of AI-powered development tools.
        🚀 No vendor lock-in, just pure innovation.
      </>
    ),
  },
];

function Feature({title, Svg, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
