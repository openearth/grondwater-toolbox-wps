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
                <ColorMapEntry color="#000000" opacity="1.0" quantity="{q0}" label="{q0} m NAP" />
                <ColorMapEntry color="#081c76" opacity="1.0" quantity="{q1}" label="{q1}" />
                <ColorMapEntry color="#16487a" opacity="1.0" quantity="{q2}" label="{q2}" />
                <ColorMapEntry color="#f7f8ab" opacity="1.0" quantity="{q3}" label="{q3}" />
                <ColorMapEntry color="#3eb032" opacity="1.0" quantity="{q4}" label="{q4}" />
                <ColorMapEntry color="#3f8b3b" opacity="1.0" quantity="{q5}" label="{q5}" />
                <ColorMapEntry color="#c5b01d" opacity="1.0" quantity="{q6}" label="{q6}" />
                <ColorMapEntry color="#d36602" opacity="1.0" quantity="{q7}" label="{q7}" />
                <ColorMapEntry color="#870800" opacity="1.0" quantity="{q8}" label="{q8}" />
                <ColorMapEntry color="#6f1f07" opacity="1.0" quantity="{q9}" label="{q9}" />
                <ColorMapEntry color="#713917" opacity="1.0" quantity="{q10}" label="{q10}" />
                <ColorMapEntry color="#977967" opacity="1.0" quantity="{q11}" label="{q11}" />
                <ColorMapEntry color="#c0c0c0" opacity="1.0" quantity="{q12}" label="{q12}" />
                <ColorMapEntry color="#ebe9eb" opacity="1.0" quantity="{q13}" label="{q13} m NAP" />
              </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
