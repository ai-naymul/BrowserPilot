import { Entity } from '@/types/entity';
import { ContactCardWidget } from '@/components/widgets/ContactCardWidget';

interface ContextPanelProps {
  entity: Entity | null;
  allEntities?: Entity[];
  dependencies?: any[];
}

export const ContextPanel = ({ entity, allEntities, dependencies }: ContextPanelProps) => {
  if (!entity) {
    return (
      <div className="w-80 bg-context border-l border-border overflow-y-auto">
        <div className="p-6 text-center text-muted-foreground">
          <p>No context available</p>
        </div>
      </div>
    );
  }



  // Check for contact data
  const contactsAttr = entity.attributes.find(
    (attr) => attr.widget === 'array' && attr.item_widget === 'contact_card'
  );

  // Check for menu items
  const menuItems = entity.children?.filter((child) => 
    child.type.toLowerCase().includes('recipe') || 
    child.type.toLowerCase().includes('menu')
  );

  return (
    <div className="w-80 bg-context border-l border-border overflow-y-auto">

      {/* Contacts */}
      {contactsAttr && (
        <div className="p-4">
          <h3 className="text-sm font-semibold mb-3">Guests</h3>
          <div className="space-y-3">
            {(contactsAttr.value as any[]).map((contact, idx) => (
              <ContactCardWidget
                key={idx}
                attribute={{ ...contactsAttr, value: contact }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Menu Items */}
      {menuItems && menuItems.length > 0 && (
        <div className="p-4 border-t border-border">
          <h3 className="text-sm font-semibold mb-3">Menu</h3>
          <div className="space-y-3">
            {menuItems.map((item) => (
              <div key={item.id} className="border border-border rounded-lg p-3">
                <h4 className="font-medium mb-2">{item.public_identifier}</h4>
                {item.attributes.map((attr) => (
                  <div key={attr.name} className="text-xs text-muted-foreground">
                    <span className="capitalize">{attr.name.replace('_', ' ')}: </span>
                    <span>{attr.value.toString()}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Related Areas List */}
      {entity.children && entity.children.length > 0 && !contactsAttr && !menuItems && (
        <div className="p-4">
          <h3 className="text-sm font-semibold mb-3">Related Items</h3>
          <div className="space-y-2">
            {entity.children.map((child) => (
              <div
                key={child.id}
                className="p-3 border border-border rounded-lg hover:border-accent transition-colors cursor-pointer"
              >
                <div className="font-medium text-sm">{child.public_identifier}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
