import { EntityAttribute } from '@/types/entity';
import { Mail, Phone, Leaf } from 'lucide-react';

interface ContactCardWidgetProps {
  attribute: EntityAttribute;
}

export const ContactCardWidget = ({ attribute }: ContactCardWidgetProps) => {
  const contact = attribute.value;
  
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const isDietary = contact.dietary || contact.dietaryRestrictions;

  return (
    <div className="border border-border rounded-lg p-4 bg-card hover:border-accent transition-colors">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-semibold flex-shrink-0">
          {getInitials(contact.name)}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium mb-1">{contact.name}</h4>
          {contact.email && (
            <div className="flex items-center gap-1.5 text-sm text-muted-foreground mb-1">
              <Mail className="h-3 w-3" />
              <span className="truncate">{contact.email}</span>
            </div>
          )}
          {contact.phone && (
            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <Phone className="h-3 w-3" />
              <span>{contact.phone}</span>
            </div>
          )}
        </div>
      </div>
      
      {isDietary && (
        <div className="mt-3 flex gap-1.5 flex-wrap">
          {(Array.isArray(contact.dietary) ? contact.dietary : [contact.dietary])
            .filter(Boolean)
            .map((restriction: string) => (
              <span
                key={restriction}
                className="inline-flex items-center gap-1 px-2 py-1 bg-tag-dietary/10 text-tag-dietary rounded text-xs font-medium"
              >
                <Leaf className="h-3 w-3" />
                {restriction}
              </span>
            ))}
        </div>
      )}
    </div>
  );
};
