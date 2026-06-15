import SimpleBubble from './SimpleBubble.jsx'
import ConsultationBubble from './ConsultationBubble.jsx'
import ContractResultBubble from './ContractResultBubble.jsx'
import CollectingBubble from './CollectingBubble.jsx'
import ConfirmingBubble from './ConfirmingBubble.jsx'
import DownloadBubble from './DownloadBubble.jsx'
import DocSelectorBubble from './DocSelectorBubble.jsx'
import GuidanceBubble from './GuidanceBubble.jsx'
import QnaGuideBubble from './QnaGuideBubble.jsx'

/**
 * kind 에 따라 올바른 봇 메시지 컴포넌트를 선택해 렌더링하는 디스패처
 *
 * @param {{ msg: object, onSend: (text: string, docType?: string) => void,
 *           onDocTypeSelect: (type: string) => void, onCancel: () => void }} props
 */
export default function BotMessage({ msg, onSend, onDocTypeSelect, onCancel }) {
  switch (msg.kind) {
    case 'consultation':
      return (
        <ConsultationBubble
          content={msg.content}
          legal_grounds={msg.legal_grounds}
          sources={msg.sources}
          suggest_document={msg.suggest_document ?? false}
          document_type={msg.document_type ?? null}
          onDocTypeSelect={onDocTypeSelect}
        />
      )
    case 'contract':
      return (
        <ContractResultBubble
          analyzed={msg.analyzed}
          violations={msg.violations}
          content={msg.content}
          used_vision={msg.used_vision ?? false}
        />
      )
    case 'collecting':
      return <CollectingBubble content={msg.content} choices={msg.choices ?? []} onSend={onSend} />
    case 'confirming':
      return (
        <ConfirmingBubble
          content={msg.content}
          onConfirm={() => onSend('맞아요')}
          onEdit={() => onSend('고칠래요')}
        />
      )
    case 'download':
      return <DownloadBubble content={msg.content} download_url={msg.download_url} />
    case 'doc_selector':
      return <DocSelectorBubble onDocTypeSelect={onDocTypeSelect} />
    case 'guidance':
      return (
        <GuidanceBubble
          doc_type={msg.doc_type}
          onStart={(dt) => onSend('시작하기', dt)}
          onCancel={onCancel}
        />
      )
    case 'qna-guide':
      return <QnaGuideBubble onSend={onSend} />
    default:
      return <SimpleBubble content={msg.content} />
  }
}
