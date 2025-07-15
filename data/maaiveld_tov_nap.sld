<?xml version="1.0" encoding="ISO-8859-1"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>gtopo</Name>
    <UserStyle>
      <Name>dem</Name>
      <Title>Simple DEM_and_Bath style</Title>
      <Abstract>Classic elevation and batymetry color progression</Abstract>
      <FeatureTypeStyle>
        <Rule>
          <MaxScaleDenominator>5000000</MaxScaleDenominator>
          <RasterSymbolizer>
              <ColorMap>
                <ColorMapEntry color="#000000" opacity="1.0" quantity="-50" label="-50 m NAP" />
                <ColorMapEntry color="#081c76" opacity="1.0" quantity="-5" label="-5" />
                <ColorMapEntry color="#16487a" opacity="1.0" quantity="-2" label="-2" />
                <ColorMapEntry color="#f7f8ab" opacity="1.0" quantity="-1" label="-1" />
                <ColorMapEntry color="#3eb032" opacity="1.0" quantity="0" label="0" />
                <ColorMapEntry color="#3f8b3b" opacity="1.0" quantity="5" label="5" />
                <ColorMapEntry color="#c5b01d" opacity="1.0" quantity="10" label="10" />
                <ColorMapEntry color="#d36602" opacity="1.0" quantity="25" label="25" />
                <ColorMapEntry color="#870800" opacity="1.0" quantity="50" label="50" />
                <ColorMapEntry color="#6f1f07" opacity="1.0" quantity="75" label="75" />
                <ColorMapEntry color="#713917" opacity="1.0" quantity="100" label="100" />
                <ColorMapEntry color="#977967" opacity="1.0" quantity="150" label="150" />
                <ColorMapEntry color="#c0c0c0" opacity="1.0" quantity="200" label="200" />
                <ColorMapEntry color="#ebe9eb" opacity="1.0" quantity="250" label="250 m NAP" />
              </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
