import { Component, inject, signal, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

// PrimeNG imports
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { ToastModule } from 'primeng/toast';
import { TimelineModule } from 'primeng/timeline';
import { TableModule } from 'primeng/table';
import { PanelModule } from 'primeng/panel';
import { BadgeModule } from 'primeng/badge';
import { DividerModule } from 'primeng/divider';

// Services
import { TranslateModule } from '@ngx-translate/core';
import { EventService, Event, EventListItem } from '../../core/services/event.service';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-event-detail',
  standalone: true,
  imports: [
    CommonModule,
    CardModule,
    ButtonModule,
    TagModule,
    TooltipModule,
    ToastModule,
    TimelineModule,
    TableModule,
    PanelModule,
    BadgeModule,
    DividerModule,
    TranslateModule,
  ],
  providers: [MessageService],
  templateUrl: './event-detail.component.html',
})
export class EventDetailComponent implements OnInit {
  private eventService = inject(EventService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private messageService = inject(MessageService);

  // State
  event = signal<Event | null>(null);
  relatedEvents = signal<EventListItem[]>([]);
  loading = signal(false);
  loadingRelated = signal(false);
  
  // Event ID from route
  eventId = signal<number | null>(null);

  ngOnInit() {
    // Get event ID from route
    const id = this.route.snapshot.paramMap.get('id');
    if (id && id !== 'new') {
      this.eventId.set(parseInt(id, 10));
      this.loadEvent();
    } else {
      // Handle new event creation (would be implemented later)
      this.router.navigate(['/events']);
    }
  }

  loadEvent() {
    const id = this.eventId();
    if (!id) return;
    
    this.loading.set(true);
    this.eventService.getById(id).subscribe({
      next: (event) => {
        this.event.set(event);
        this.loading.set(false);
        this.loadRelatedEvents();
      },
      error: (error) => {
        console.error('Error loading event:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load event details',
        });
        this.loading.set(false);
      },
    });
  }

  loadRelatedEvents() {
    const event = this.event();
    if (!event) return;

    this.loadingRelated.set(true);
    
    // Load events for the same entity
    this.eventService.load({
      entity_type: event.entity_type,
      entity_id: event.entity_id,
    }).subscribe({
      next: (events) => {
        // Filter out the current event and limit to recent related events
        const related = events
          .filter(e => e.id !== event.id)
          .slice(0, 10); // Show last 10 related events
        this.relatedEvents.set(related);
        this.loadingRelated.set(false);
      },
      error: (error) => {
        console.error('Error loading related events:', error);
        this.loadingRelated.set(false);
      },
    });
  }

  goBack() {
    this.router.navigate(['/events']);
  }

  getSeverityColor(severity: string): 'success' | 'warning' | 'danger' | 'info' | 'secondary' {
    switch (severity) {
      case 'critical':
        return 'danger';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'secondary';
      case 'info':
      default:
        return 'success';
    }
  }

  getEventTypeIcon(eventType: string): string {
    return this.eventService.getEventTypeIcon(eventType as any);
  }

  formatTimestamp(timestamp: string): string {
    return this.eventService.formatTimestamp(timestamp);
  }

  getRelativeTime(timestamp: string): string {
    return this.eventService.getRelativeTime(timestamp);
  }

  isRecent(timestamp: string): boolean {
    return this.eventService.isRecent(timestamp);
  }

  getEntityDisplayInfo(event: Event | EventListItem): string {
    if (event.entity_info) {
      const info = event.entity_info;
      switch (event.entity_type) {
        case 'product':
          return `${info.name} (${info.gtin || 'N/A'})`;
        case 'batch':
          return `${info.name} - ${info.product_name || 'Unknown Product'}`;
        case 'pack':
          return `${info.name} - ${info.product_name || 'Unknown Product'}`;
        case 'shipment':
          return `${info.name} (${info.carrier || 'Unknown Carrier'})`;
        default:
          return info.name;
      }
    }
    return `${event.entity_type}#${event.entity_id}`;
  }

  getMetadataEntries(): { key: string; value: any }[] {
    const event = this.event();
    if (!event || !event.metadata || typeof event.metadata !== 'object') {
      return [];
    }
    
    return Object.entries(event.metadata).map(([key, value]) => ({
      key,
      value: typeof value === 'object' ? JSON.stringify(value, null, 2) : value
    }));
  }

  getSystemInfoEntries(): { key: string; value: any }[] {
    const event = this.event();
    if (!event || !event.system_info || typeof event.system_info !== 'object') {
      return [];
    }
    
    return Object.entries(event.system_info).map(([key, value]) => ({
      key,
      value: typeof value === 'object' ? JSON.stringify(value, null, 2) : value
    }));
  }

  navigateToEntity() {
    const event = this.event();
    if (!event) return;

    // Navigate to the related entity based on type
    switch (event.entity_type) {
      case 'product':
        this.router.navigate(['/products', event.entity_id]);
        break;
      case 'batch':
        this.router.navigate(['/batches', event.entity_id]);
        break;
      case 'pack':
        this.router.navigate(['/packs', event.entity_id]);
        break;
      case 'shipment':
        this.router.navigate(['/shipments', event.entity_id]);
        break;
      default:
        this.messageService.add({
          severity: 'info',
          summary: 'Info',
          detail: 'Navigation not available for this entity type',
        });
    }
  }

  viewRelatedEvent(relatedEvent: EventListItem) {
    this.router.navigate(['/events', relatedEvent.id]);
  }

  // Timeline event customization for related events
  getTimelineEvents() {
    return this.relatedEvents().map(event => ({
      ...event,
      icon: this.getEventTypeIcon(event.event_type),
      color: this.getSeverityColor(event.severity),
      relativeTime: this.getRelativeTime(event.timestamp),
      entityDisplay: this.getEntityDisplayInfo(event),
      isRecent: this.isRecent(event.timestamp)
    }));
  }

  copyToClipboard(text: string) {
    navigator.clipboard.writeText(text).then(() => {
      this.messageService.add({
        severity: 'success',
        summary: 'Copied',
        detail: 'Text copied to clipboard',
      });
    }).catch(() => {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to copy to clipboard',
      });
    });
  }
}
