import { Entity, ChatMessage } from '@/types/entity';

export const movingPlanEntity: Entity = {
  id: 'moving_plan_1',
  type: 'Moving_Plan',
  icon: '🚚',
  public_identifier: 'San Francisco Move',
  attributes: [
    {
      name: 'destination',
      value: 'San Francisco, CA',
      widget: 'location',
      function: 'publicIdentifier',
    },
    {
      name: 'move_date',
      value: '2024-09-19',
      widget: 'date',
    },
    {
      name: 'budget',
      value: 3500,
      widget: 'currency',
    },
  ],
  children: [
    {
      id: 'area_1',
      type: 'Area',
      icon: '🏘️',
      public_identifier: 'Mission District',
      attributes: [
        { name: 'avg_rent', value: 3200, widget: 'currency' },
        { name: 'lifestyle', value: '3 Missing', widget: 'short_text' },
      ],
    },
    {
      id: 'area_2',
      type: 'Area',
      icon: '🏘️',
      public_identifier: 'Nob Hill',
      attributes: [
        { name: 'avg_rent', value: 3200, widget: 'currency' },
        { name: 'lifestyle', value: '3 Lack', widget: 'short_text' },
      ],
    },
    {
      id: 'area_3',
      type: 'Area',
      icon: '🏘️',
      public_identifier: 'SoMa',
      attributes: [
        { name: 'avg_rent', value: 2800, widget: 'currency' },
        { name: 'lifestyle', value: '0 Livable', widget: 'short_text' },
      ],
    },
    {
      id: 'safety_1',
      type: 'Safety_Info',
      icon: '🛡️',
      public_identifier: 'Safety Rating',
      tags: ['SAFETY_INFO'],
      attributes: [
        { name: 'rating', value: '8/10', widget: 'short_text' },
      ],
    },
  ],
};

export const dinnerPartyEntity: Entity = {
  id: 'dinner_party_1',
  type: 'Dinner_Party',
  icon: '🍽️',
  public_identifier: 'Dinner Party',
  attributes: [
    {
      name: 'date',
      value: '2024-09-27',
      widget: 'date',
    },
    {
      name: 'time',
      value: '19:00',
      widget: 'time',
    },
    {
      name: 'location',
      value: '985 Sutter St, San Francisco',
      widget: 'location',
    },
    {
      name: 'guests',
      value: [
        {
          name: 'Alice Johnson',
          email: 'alice@jelly-ui.app',
          phone: '617-200-1785',
          dietary: 'Vegan',
        },
        {
          name: 'Millie',
          email: 'millie@jelly-ui.app',
          phone: '017-175-9701',
          dietary: 'Vegan',
        },
        {
          name: 'Sarah',
          email: 'sarah@jelly-ui.app',
          phone: '017-175-3520',
        },
        {
          name: 'Mike Wilson',
          email: 'mike@jelly-ui.app',
          phone: '617-200-1785',
        },
      ],
      widget: 'array',
      item_widget: 'contact_card',
    },
  ],
  children: [
    {
      id: 'menu_1',
      type: 'Recipe',
      icon: '🥗',
      public_identifier: 'Vegan Mapo Tofu',
      attributes: [
        { name: 'cuisine_type', value: 'Chinese', widget: 'short_text' },
        { name: 'ingredients', value: 'Silken Tofu, Doubanjiang, Sichuan Pepper', widget: 'short_text' },
        { name: 'dietary_suitability', value: 'Vegan', widget: 'short_text' },
      ],
    },
    {
      id: 'menu_2',
      type: 'Recipe',
      icon: '🥘',
      public_identifier: 'Vegan Bibimbap',
      attributes: [
        { name: 'cuisine_type', value: 'Korean', widget: 'short_text' },
        { name: 'ingredients', value: 'Steamed Rice, Gochujang, Tofu, Spinach', widget: 'short_text' },
        { name: 'dietary_suitability', value: 'Vegan', widget: 'short_text' },
      ],
    },
    {
      id: 'menu_3',
      type: 'Recipe',
      icon: '🍛',
      public_identifier: 'Vegan Green Curry',
      attributes: [
        { name: 'cuisine_type', value: 'Thai', widget: 'short_text' },
        { name: 'ingredients', value: 'Tofu, Green Curry Paste, Coconut Milk', widget: 'short_text' },
        { name: 'dietary_suitability', value: 'Vegan', widget: 'short_text' },
      ],
    },
  ],
};

export const initialMessages: ChatMessage[] = [
  {
    id: '1',
    role: 'user',
    content: "I'm moving to San Francisco",
    timestamp: new Date(),
  },
  {
    id: '2',
    role: 'assistant',
    content: "I'm helping you find a place to live. Tell me about the different areas you're interested in.",
    timestamp: new Date(),
  },
];

export const dinnerMessages: ChatMessage[] = [
  {
    id: '1',
    role: 'user',
    content: "I'm hosting a dinner party with my friends",
    timestamp: new Date(),
  },
  {
    id: '2',
    role: 'assistant',
    content: "Who are you going to invite?",
    timestamp: new Date(),
  },
  {
    id: '3',
    role: 'user',
    content: "Alice, Sarah, Mike, and a few others",
    timestamp: new Date(),
  },
  {
    id: '4',
    role: 'assistant',
    content: "I've heard some of them could be vegan. I've updated the dinner party with vegan menu options.",
    timestamp: new Date(),
  },
];
