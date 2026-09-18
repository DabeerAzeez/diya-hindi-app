import React from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

// Helper to recursively parse inline markdown (bold, italic, code, br)
function parseInlineMarkdown(text, keyPrefix = 'md') {
  if (!text) return null;

  // Clean trailing <br> tags
  const cleaned = text.replace(/(?:<br\s*\/?>\s*)+$/gi, '');
  if (!cleaned) return null;

  // Regex to match: <br>, ***bold italic***, **bold**, *italic*, `code`
  const tokenRegex = /(<br\s*\/?>|\*\*\*(?:[^*]|\*(?!\*\*))+\*\*\*|\*\*(?:[^*]|\*(?!\*))+\*\*|\*(?:[^*]|\n)+\*|`[^`]+`)/gi;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = tokenRegex.exec(cleaned)) !== null) {
    if (match.index > lastIndex) {
      parts.push(cleaned.substring(lastIndex, match.index));
    }

    const token = match[0];
    const key = `${keyPrefix}-${match.index}`;

    if (/^<br\s*\/?>$/i.test(token)) {
      parts.push(<br key={key} className="my-1" />);
    } else if (token.startsWith('***') && token.endsWith('***')) {
      const inner = token.slice(3, -3);
      parts.push(
        <strong key={key} className="font-bold text-white">
          <em className="italic">{parseInlineMarkdown(inner, `${key}-inner`)}</em>
        </strong>
      );
    } else if (token.startsWith('**') && token.endsWith('**')) {
      const inner = token.slice(2, -2);
      parts.push(
        <strong key={key} className="font-bold text-white">
          {parseInlineMarkdown(inner, `${key}-inner`)}
        </strong>
      );
    } else if (token.startsWith('*') && token.endsWith('*')) {
      const inner = token.slice(1, -1);
      parts.push(
        <em key={key} className="italic text-slate-200">
          {parseInlineMarkdown(inner, `${key}-inner`)}
        </em>
      );
    } else if (token.startsWith('`') && token.endsWith('`')) {
      const inner = token.slice(1, -1);
      parts.push(
        <code
          key={key}
          className="px-1.5 py-0.5 rounded bg-[#1e293b] text-amber-300 text-xs font-mono border border-[#243049]"
        >
          {inner}
        </code>
      );
    } else {
      parts.push(token);
    }

    lastIndex = tokenRegex.lastIndex;
  }

  if (lastIndex < cleaned.length) {
    parts.push(cleaned.substring(lastIndex));
  }

  if (parts.length === 0) return cleaned;
  return parts.map((part, idx) => (
    <React.Fragment key={idx}>{part}</React.Fragment>
  ));
}

export function RenderMath({ text, className = '' }) {
  if (!text) return null;

  // Clean trailing <br> tags first
  const strText = typeof text === 'string' ? text.replace(/(?:<br\s*\/?>\s*)+$/gi, '') : String(text);

  const parts = [];
  const mathRegex = /(\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$)/g;
  let match;
  let lastIndex = 0;

  while ((match = mathRegex.exec(strText)) !== null) {
    if (match.index > lastIndex) {
      const textChunk = strText.substring(lastIndex, match.index);
      parts.push({
        type: 'rich_text',
        content: parseInlineMarkdown(textChunk, `txt-${lastIndex}`)
      });
    }

    const raw = match[0];
    const isDisplay = raw.startsWith('$$');
    const expr = isDisplay ? raw.slice(2, -2).trim() : raw.slice(1, -1).trim();

    try {
      const html = katex.renderToString(expr, {
        displayMode: isDisplay,
        throwOnError: false
      });
      parts.push({ type: 'math', html, isDisplay });
    } catch (e) {
      parts.push({ type: 'rich_text', content: raw });
    }

    lastIndex = mathRegex.lastIndex;
  }

  if (lastIndex < strText.length) {
    const remainingText = strText.substring(lastIndex);
    parts.push({
      type: 'rich_text',
      content: parseInlineMarkdown(remainingText, `txt-${lastIndex}`)
    });
  }

  if (parts.length === 0) {
    return <span className={className}>{parseInlineMarkdown(strText, 'single')}</span>;
  }

  return (
    <span className={className}>
      {parts.map((part, i) => {
        if (part.type === 'math') {
          return (
            <span
              key={i}
              dangerouslySetInnerHTML={{ __html: part.html }}
              className={part.isDisplay ? 'block my-3 text-center overflow-x-auto py-1 text-amber-200' : 'inline-block align-middle my-0.5 mx-1'}
            />
          );
        }
        return <React.Fragment key={i}>{part.content}</React.Fragment>;
      })}
    </span>
  );
}

export default RenderMath;
