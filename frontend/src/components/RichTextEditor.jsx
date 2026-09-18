import React, { useEffect, useRef } from 'react';
import Quill from 'quill';
import 'quill/dist/quill.snow.css';

export default function RichTextEditor({ value, onChange, placeholder, minHeight = '140px' }) {
  const containerRef = useRef(null);
  const quillRef = useRef(null);
  const isInternalChangeRef = useRef(false);

  useEffect(() => {
    if (!containerRef.current) return;

    // Reset container for strict mode mount / unmount safety
    containerRef.current.innerHTML = '';
    const editorDiv = document.createElement('div');
    containerRef.current.appendChild(editorDiv);

    const quill = new Quill(editorDiv, {
      theme: 'snow',
      placeholder: placeholder || '',
      modules: {
        toolbar: [
          [{ header: [1, 2, 3, false] }],
          ['bold', 'italic', 'underline', 'strike'],
          [{ list: 'ordered' }, { list: 'bullet' }],
          ['clean'],
        ],
      },
    });

    quillRef.current = quill;

    if (value) {
      if (/<[a-z][\s\S]*>/i.test(value)) {
        quill.clipboard.dangerouslyPasteHTML(value);
      } else {
        quill.setText(value);
      }
    }

    quill.on('text-change', () => {
      if (isInternalChangeRef.current) return;
      const html = quill.root.innerHTML;
      const clean = html === '<p><br></p>' ? '' : html;
      onChange?.(clean);
    });

    return () => {
      quillRef.current = null;
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, []);

  // Update content when value prop changes externally
  useEffect(() => {
    const quill = quillRef.current;
    if (!quill) return;

    const currentHtml = quill.root.innerHTML;
    const targetValue = value || '';

    // Only update if genuinely different to preserve cursor and avoid loops
    if (targetValue !== currentHtml && (targetValue !== '' || currentHtml !== '<p><br></p>')) {
      isInternalChangeRef.current = true;
      if (/<[a-z][\s\S]*>/i.test(targetValue)) {
        quill.clipboard.dangerouslyPasteHTML(targetValue);
      } else {
        quill.setText(targetValue);
      }
      isInternalChangeRef.current = false;
    }
  }, [value]);

  return (
    <div 
      ref={containerRef}
      className="rich-text-container rounded-xl overflow-hidden text-slate-100"
      style={{ '--editor-min-height': minHeight }}
    />
  );
}
