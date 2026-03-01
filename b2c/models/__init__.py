# b2c/models/__init__.py

# Customer models
from .customer import (
    Customer,
    CustomerProfile,
    TravelCompanion,
)

# Loyalty models
from .loyalty import (
    LoyaltyProgram,
    LoyaltyTransaction,
    Reward,
    CustomerReward,
)

# Wishlist models
from .wishlist import (
    Wishlist,
    WishlistItem,
    FavoriteDestination,
    FavoriteAirline,
)

# Review models
from .reviews import (
    Review,
    ReviewImage,
    ReviewResponse,
)

# Alert models
from .alerts import (
    PriceAlert,
    TravelAlert,
    NewsletterSubscription,
)

# Social models
from .social import (
    TravelStory,
    TravelPhoto,
    StoryLike,
    StoryComment,
)

# Trip models
from .trips import (
    Trip,
    TripDay,
    TripActivity,
)

# Support models
from .support import (
    SupportTicket,
    TicketMessage,
    TicketAttachment,
    FAQ,
)

# Wallet models
from .wallet import (
    CustomerWallet,
    WalletTransaction,
    SavedPaymentMethod,
)

# Referral models
from .referrals import (
    ReferralProgram,
    CustomerReferral,
    AffiliatePartner,
    AffiliateClick,
)

__all__ = [
    # Customer
    'Customer',
    'CustomerProfile',
    'TravelCompanion',
    
    # Loyalty
    'LoyaltyProgram',
    'LoyaltyTransaction',
    'Reward',
    'CustomerReward',
    
    # Wishlist
    'Wishlist',
    'WishlistItem',
    'FavoriteDestination',
    'FavoriteAirline',
    
    # Reviews
    'Review',
    'ReviewImage',
    'ReviewResponse',
    
    # Alerts
    'PriceAlert',
    'TravelAlert',
    'NewsletterSubscription',
    
    # Social
    'TravelStory',
    'TravelPhoto',
    'StoryLike',
    'StoryComment',
    
    # Trips
    'Trip',
    'TripDay',
    'TripActivity',
    
    # Support
    'SupportTicket',
    'TicketMessage',
    'TicketAttachment',
    'FAQ',
    
    # Wallet
    'CustomerWallet',
    'WalletTransaction',
    'SavedPaymentMethod',
    
    # Referrals
    'ReferralProgram',
    'CustomerReferral',
    'AffiliatePartner',
    'AffiliateClick',
]
