export interface EntityAttribute {
  name: string;
  value: any;
  data_type?: string;
  widget?: string;
  item_widget?: string;
  function?: string;
  editable?: boolean;
  validation?: any;
  metadata?: Record<string, any>;
}

export interface Entity {
  id: string;
  type: string;
  icon?: string;
  color?: string;
  public_identifier: string;
  attributes: EntityAttribute[];
  children?: Entity[];
  tags?: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}
