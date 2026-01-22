#![allow(clippy::redundant_closure_call)]
#![allow(clippy::needless_lifetimes)]
#![allow(clippy::match_single_binding)]
#![allow(clippy::clone_on_copy)]

#[doc = r" Error types."]
pub mod error {
    #[doc = r" Error from a `TryFrom` or `FromStr` implementation."]
    pub struct ConversionError(::std::borrow::Cow<'static, str>);
    impl ::std::error::Error for ConversionError {}
    impl ::std::fmt::Display for ConversionError {
        fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> Result<(), ::std::fmt::Error> {
            ::std::fmt::Display::fmt(&self.0, f)
        }
    }
    impl ::std::fmt::Debug for ConversionError {
        fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> Result<(), ::std::fmt::Error> {
            ::std::fmt::Debug::fmt(&self.0, f)
        }
    }
    impl From<&'static str> for ConversionError {
        fn from(value: &'static str) -> Self {
            Self(value.into())
        }
    }
    impl From<String> for ConversionError {
        fn from(value: String) -> Self {
            Self(value.into())
        }
    }
}
#[doc = "Message for ACL accounts\n\nArgs:\n    accounts (dict): ACL accounts"]
#[doc = r""]
#[doc = r" <details><summary>JSON schema</summary>"]
#[doc = r""]
#[doc = r" ```json"]
#[doc = "{"]
#[doc = "  \"title\": \"ACLAccountsMessage\","]
#[doc = "  \"description\": \"Message for ACL accounts\\n\\nArgs:\\n    accounts (dict): ACL accounts\","]
#[doc = "  \"type\": \"object\","]
#[doc = "  \"required\": ["]
#[doc = "    \"accounts\""]
#[doc = "  ],"]
#[doc = "  \"properties\": {"]
#[doc = "    \"accounts\": {"]
#[doc = "      \"title\": \"Accounts\","]
#[doc = "      \"type\": \"object\","]
#[doc = "      \"additionalProperties\": {"]
#[doc = "        \"type\": \"object\","]
#[doc = "        \"additionalProperties\": {"]
#[doc = "          \"anyOf\": ["]
#[doc = "            {"]
#[doc = "              \"type\": \"array\","]
#[doc = "              \"items\": {"]
#[doc = "                \"type\": \"string\""]
#[doc = "              }"]
#[doc = "            },"]
#[doc = "            {"]
#[doc = "              \"type\": \"string\""]
#[doc = "            }"]
#[doc = "          ]"]
#[doc = "        },"]
#[doc = "        \"propertyNames\": {"]
#[doc = "          \"enum\": ["]
#[doc = "            \"categories\","]
#[doc = "            \"keys\","]
#[doc = "            \"channels\","]
#[doc = "            \"commands\","]
#[doc = "            \"profile\""]
#[doc = "          ]"]
#[doc = "        }"]
#[doc = "      }"]
#[doc = "    },"]
#[doc = "    \"metadata\": {"]
#[doc = "      \"title\": \"Metadata\","]
#[doc = "      \"type\": \"object\","]
#[doc = "      \"additionalProperties\": true"]
#[doc = "    }"]
#[doc = "  }"]
#[doc = "}"]
#[doc = r" ```"]
#[doc = r" </details>"]
#[derive(:: serde :: Deserialize, :: serde :: Serialize, Clone, Debug)]
pub struct AclAccountsMessage {
    pub accounts: ::std::collections::HashMap<
        ::std::string::String,
        ::std::collections::HashMap<
            AclAccountsMessageAccountsValueKey,
            AclAccountsMessageAccountsValueValue,
        >,
    >,
    #[serde(default, skip_serializing_if = "::serde_json::Map::is_empty")]
    pub metadata: ::serde_json::Map<::std::string::String, ::serde_json::Value>,
}
impl ::std::convert::From<&AclAccountsMessage> for AclAccountsMessage {
    fn from(value: &AclAccountsMessage) -> Self {
        value.clone()
    }
}
impl AclAccountsMessage {
    pub fn builder() -> builder::AclAccountsMessage {
        Default::default()
    }
}
#[doc = "`AclAccountsMessageAccountsValueKey`"]
#[doc = r""]
#[doc = r" <details><summary>JSON schema</summary>"]
#[doc = r""]
#[doc = r" ```json"]
#[doc = "{"]
#[doc = "  \"type\": \"string\","]
#[doc = "  \"enum\": ["]
#[doc = "    \"categories\","]
#[doc = "    \"keys\","]
#[doc = "    \"channels\","]
#[doc = "    \"commands\","]
#[doc = "    \"profile\""]
#[doc = "  ]"]
#[doc = "}"]
#[doc = r" ```"]
#[doc = r" </details>"]
#[derive(
    :: serde :: Deserialize,
    :: serde :: Serialize,
    Clone,
    Copy,
    Debug,
    Eq,
    Hash,
    Ord,
    PartialEq,
    PartialOrd,
)]
pub enum AclAccountsMessageAccountsValueKey {
    #[serde(rename = "categories")]
    Categories,
    #[serde(rename = "keys")]
    Keys,
    #[serde(rename = "channels")]
    Channels,
    #[serde(rename = "commands")]
    Commands,
    #[serde(rename = "profile")]
    Profile,
}
impl ::std::convert::From<&Self> for AclAccountsMessageAccountsValueKey {
    fn from(value: &AclAccountsMessageAccountsValueKey) -> Self {
        value.clone()
    }
}
impl ::std::fmt::Display for AclAccountsMessageAccountsValueKey {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        match *self {
            Self::Categories => f.write_str("categories"),
            Self::Keys => f.write_str("keys"),
            Self::Channels => f.write_str("channels"),
            Self::Commands => f.write_str("commands"),
            Self::Profile => f.write_str("profile"),
        }
    }
}
impl ::std::str::FromStr for AclAccountsMessageAccountsValueKey {
    type Err = self::error::ConversionError;
    fn from_str(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        match value {
            "categories" => Ok(Self::Categories),
            "keys" => Ok(Self::Keys),
            "channels" => Ok(Self::Channels),
            "commands" => Ok(Self::Commands),
            "profile" => Ok(Self::Profile),
            _ => Err("invalid value".into()),
        }
    }
}
impl ::std::convert::TryFrom<&str> for AclAccountsMessageAccountsValueKey {
    type Error = self::error::ConversionError;
    fn try_from(value: &str) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<&::std::string::String> for AclAccountsMessageAccountsValueKey {
    type Error = self::error::ConversionError;
    fn try_from(
        value: &::std::string::String,
    ) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
impl ::std::convert::TryFrom<::std::string::String> for AclAccountsMessageAccountsValueKey {
    type Error = self::error::ConversionError;
    fn try_from(
        value: ::std::string::String,
    ) -> ::std::result::Result<Self, self::error::ConversionError> {
        value.parse()
    }
}
#[doc = "`AclAccountsMessageAccountsValueValue`"]
#[doc = r""]
#[doc = r" <details><summary>JSON schema</summary>"]
#[doc = r""]
#[doc = r" ```json"]
#[doc = "{"]
#[doc = "  \"anyOf\": ["]
#[doc = "    {"]
#[doc = "      \"type\": \"array\","]
#[doc = "      \"items\": {"]
#[doc = "        \"type\": \"string\""]
#[doc = "      }"]
#[doc = "    },"]
#[doc = "    {"]
#[doc = "      \"type\": \"string\""]
#[doc = "    }"]
#[doc = "  ]"]
#[doc = "}"]
#[doc = r" ```"]
#[doc = r" </details>"]
#[derive(:: serde :: Deserialize, :: serde :: Serialize, Clone, Debug)]
#[serde(untagged)]
pub enum AclAccountsMessageAccountsValueValue {
    Array(::std::vec::Vec<::std::string::String>),
    String(::std::string::String),
}
impl ::std::convert::From<&Self> for AclAccountsMessageAccountsValueValue {
    fn from(value: &AclAccountsMessageAccountsValueValue) -> Self {
        value.clone()
    }
}
impl ::std::convert::From<::std::vec::Vec<::std::string::String>>
    for AclAccountsMessageAccountsValueValue
{
    fn from(value: ::std::vec::Vec<::std::string::String>) -> Self {
        Self::Array(value)
    }
}
#[doc = r" Types for composing complex structures."]
pub mod builder {
    #[derive(Clone, Debug)]
    pub struct AclAccountsMessage {
        accounts: ::std::result::Result<
            ::std::collections::HashMap<
                ::std::string::String,
                ::std::collections::HashMap<
                    super::AclAccountsMessageAccountsValueKey,
                    super::AclAccountsMessageAccountsValueValue,
                >,
            >,
            ::std::string::String,
        >,
        metadata: ::std::result::Result<
            ::serde_json::Map<::std::string::String, ::serde_json::Value>,
            ::std::string::String,
        >,
    }
    impl ::std::default::Default for AclAccountsMessage {
        fn default() -> Self {
            Self {
                accounts: Err("no value supplied for accounts".to_string()),
                metadata: Ok(Default::default()),
            }
        }
    }
    impl AclAccountsMessage {
        pub fn accounts<T>(mut self, value: T) -> Self
        where
            T: ::std::convert::TryInto<
                ::std::collections::HashMap<
                    ::std::string::String,
                    ::std::collections::HashMap<
                        super::AclAccountsMessageAccountsValueKey,
                        super::AclAccountsMessageAccountsValueValue,
                    >,
                >,
            >,
            T::Error: ::std::fmt::Display,
        {
            self.accounts = value
                .try_into()
                .map_err(|e| format!("error converting supplied value for accounts: {}", e));
            self
        }
        pub fn metadata<T>(mut self, value: T) -> Self
        where
            T: ::std::convert::TryInto<
                ::serde_json::Map<::std::string::String, ::serde_json::Value>,
            >,
            T::Error: ::std::fmt::Display,
        {
            self.metadata = value
                .try_into()
                .map_err(|e| format!("error converting supplied value for metadata: {}", e));
            self
        }
    }
    impl ::std::convert::TryFrom<AclAccountsMessage> for super::AclAccountsMessage {
        type Error = super::error::ConversionError;
        fn try_from(
            value: AclAccountsMessage,
        ) -> ::std::result::Result<Self, super::error::ConversionError> {
            Ok(Self {
                accounts: value.accounts?,
                metadata: value.metadata?,
            })
        }
    }
    impl ::std::convert::From<super::AclAccountsMessage> for AclAccountsMessage {
        fn from(value: super::AclAccountsMessage) -> Self {
            Self {
                accounts: Ok(value.accounts),
                metadata: Ok(value.metadata),
            }
        }
    }
}
