export interface NotificationRule {
  id: number;
  user: number;
  name: string;
  event_types: string[];
  severity_levels: string[];
  channels: string[];
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationLog {
  id: number;
  event: {
    id: number;
    event_type: string;
    event_type_display: string;
    severity: string;
    severity_display: string;
    description: string;
    timestamp: string;
    entity_type: string;
    entity_type_display: string;
    entity_id: number;
    entity_display_name: string;
    location?: string;
    metadata?: any;
    is_critical: boolean;
    is_alert: boolean;
  };
  user: number;
  user_email: string;
  rule: number | null;
  channel: string;
  status: 'pending' | 'sent' | 'failed' | 'acknowledged';
  sent_at: string | null;
  acknowledged_at: string | null;
  error_message: string;
  escalated: boolean;
  escalated_to: number | null;
  escalated_at: string | null;
  created_at: string;
}

export interface NotificationRuleCreate {
  name: string;
  event_types: string[];
  severity_levels: string[];
  channels: string[];
  enabled: boolean;
}
